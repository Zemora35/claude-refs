"""Local background runner: explicit start, passive wait, no model polling or automatic retry."""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from handoff import HandoffError, compact_result, git, load_bundle, save


ACTIVE = {"queued", "running"}


def alive(pid):
    """Read-only liveness; access-denied is unknown, never permission to kill/restart."""
    if not isinstance(pid, int) or pid <= 0:
        return None
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return False if ctypes.get_last_error() == 87 else None
        try:
            code = wintypes.DWORD()
            return code.value == 259 if kernel.GetExitCodeProcess(handle, ctypes.byref(code)) else None
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return None


def now():
    return datetime.now(timezone.utc).isoformat()


def context(bundle, expected_project):
    folder, record = load_bundle(bundle)
    project = Path(record["project"]).resolve(strict=True)
    if expected_project is None or Path(expected_project).resolve(strict=True) != project:
        raise HandoffError("Task belongs to a different project; no worker was started")
    cwd = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if cwd != project:
        raise HandoffError("Run the local worker from this task's active project root")
    return folder, record


def state(folder):
    path = folder / "job.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"status": "not-launched"}


def snapshot(folder):
    result = state(folder)
    lease = folder / ("job-" + result.get("job_id", "missing") + ".launch.json")
    pid = result.get("worker_pid")
    if pid is None and lease.is_file():
        pid = json.loads(lease.read_text(encoding="utf-8")).get("launcher_pid")
    if result.get("status") in ACTIVE and alive(pid) is False:
        return {**result, "status": "interrupted", "outcome": "worker-exited-without-result",
                "note": "Worker exited without a terminal record. Inspect logs and stale locks; no automatic retry or lock removal occurred."}
    progress = folder / "progress.json"
    if progress.is_file() and result.get("status") in ACTIVE:
        current = json.loads(progress.read_text(encoding="utf-8"))
        if current.get("pid") == result.get("runner_pid"):
            result["progress"] = current
    return result


def start(bundle, expected_project, authorized=False, retry=False):
    folder, record = context(bundle, expected_project)
    if not authorized:
        return {"status": "preview", "bundle": str(folder), "claude_started": False}
    if (folder / ".running.lock").exists():
        raise HandoffError("Another run is active or has a stale lock; inspect it, do not start another worker")
    if (folder / "run-result.json").exists() and not retry:
        raise HandoffError("This bundle already ran; review its result before explicitly using --retry")
    lock = folder / ".job.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise HandoffError("A local worker is active or left a stale lock; inspect it instead of duplicating the run") from None
    identity = uuid.uuid4().hex
    with os.fdopen(fd, "w", encoding="ascii") as stream:
        stream.write(identity)
    previous = state(folder)
    if previous.get("job_id"):
        save(folder / ("job-" + previous["job_id"] + ".json"), previous)
    save(folder / "job.json", {"status": "queued", "job_id": identity, "created_at": now(),
         "project": record["project"], "bundle": str(folder), "retry": retry,
         "stdout_log": str(folder / ("job-" + identity + ".stdout.log")),
         "stderr_log": str(folder / ("job-" + identity + ".stderr.log"))})
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "_worker", "--bundle", str(folder),
               "--expected-project", record["project"], "--job-id", identity]
    if retry:
        command.append("--retry")
    kwargs = {"cwd": record["project"], "stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
              "stderr": subprocess.DEVNULL, "close_fds": True}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    try:
        child = subprocess.Popen(command, **kwargs)
    except OSError:
        save(folder / "job.json", {**state(folder), "status": "failed", "outcome": "worker-launch-failed", "finished_at": now()})
        lock.unlink(missing_ok=True)
        raise
    save(folder / ("job-" + identity + ".launch.json"), {"launcher_pid": child.pid, "job_id": identity})
    # Reap locally when the launcher is kept alive (e.g. tests); the daemon never calls a model.
    threading.Thread(target=child.wait, daemon=True).start()
    return {"status": "launched", "worker_pid": child.pid, "job_id": identity, "bundle": str(folder),
            "job_file": str(folder / "job.json"), "result_file": str(folder / "RESULT.md"),
            "claude_started": False, "note": "Local worker launched; authentication/model execution happens in the worker. No automatic chat notification is installed."}


def worker(bundle, expected_project, identity, retry=False):
    folder, record = context(bundle, expected_project)
    lock = folder / ".job.lock"
    current = state(folder)
    if not lock.is_file() or lock.read_text(encoding="ascii") != identity or current.get("job_id") != identity or current.get("status") != "queued":
        raise HandoffError("Worker identity is not the explicitly launched task")
    result_path = folder / "run-result.json"
    old_result = result_path.read_bytes() if result_path.is_file() else None
    current.update(status="running", worker_pid=os.getpid(), started_at=now())
    save(folder / "job.json", current)
    command = [sys.executable, "-B", str(Path(__file__).with_name("handoff.py")), "run", "--bundle", str(folder),
               "--expected-project", record["project"], "--start"]
    if retry:
        command.append("--retry")
    try:
        with Path(current["stdout_log"]).open("wb") as stdout, Path(current["stderr_log"]).open("wb") as stderr:
            child = subprocess.Popen(command, cwd=record["project"], stdin=subprocess.DEVNULL,
                                     stdout=stdout, stderr=stderr, shell=False)
            current["runner_pid"] = child.pid
            save(folder / "job.json", current)
            code = child.wait()
        fresh = result_path.is_file() and result_path.read_bytes() != old_result
        result = json.loads(result_path.read_text(encoding="utf-8")) if fresh else None
        current.update(status="finished" if result is not None else "failed", exit_code=code,
                       outcome=result["status"] if result is not None else "runner-failed-without-new-result",
                       finished_at=now(), result_file=str(folder / "RESULT.md"))
        if result is not None:
            current["summary"] = compact_result({k: result[k] for k in (
                "status", "changed_files", "tests_independently_verified", "verification", "automatic_merge", "automatic_push")})
        save(folder / "job.json", current)
        return current
    except (OSError, ValueError, KeyboardInterrupt) as exc:
        current.update(status="failed", outcome="worker-error", error=type(exc).__name__, finished_at=now())
        save(folder / "job.json", current)
        raise
    finally:
        if lock.is_file() and lock.read_text(encoding="ascii") == identity:
            lock.unlink()


def wait(bundle, expected_project, timeout_seconds=600):
    folder, _ = context(bundle, expected_project)
    if not 0 <= timeout_seconds <= 3600:
        raise HandoffError("Local wait must be between 0 and 3600 seconds")
    deadline = time.monotonic() + timeout_seconds
    while True:
        current = snapshot(folder)
        if current["status"] not in ACTIVE:
            return current
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return {**current, "wait_timed_out": True, "note": "Worker continues locally; no model call or retry was made by waiting"}
        time.sleep(min(.5, remaining))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("start", "wait", "_worker"):
        part = sub.add_parser(name)
        part.add_argument("--bundle", type=Path, required=True)
        part.add_argument("--expected-project", type=Path, required=True)
        if name == "start":
            part.add_argument("--start", action="store_true")
        if name in {"start", "_worker"}:
            part.add_argument("--retry", action="store_true")
        if name == "_worker":
            part.add_argument("--job-id", required=True)
        if name == "wait":
            part.add_argument("--timeout-seconds", type=int, default=600)
    args = parser.parse_args()
    try:
        if args.action == "start":
            result = start(args.bundle, args.expected_project, args.start, args.retry)
        elif args.action == "wait":
            result = wait(args.bundle, args.expected_project, args.timeout_seconds)
        else:
            result = worker(args.bundle, args.expected_project, args.job_id, args.retry)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (HandoffError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"error": str(exc), "claude_started": False}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
