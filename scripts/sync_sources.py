"""Fetch locked public source references without executing or installing them."""

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]


def git(folder, *arguments):
    hooks = PACKAGE / "scripts" / ".disabled-hooks"
    hooks.mkdir(exist_ok=True)
    command = ["git", "-c", f"core.hooksPath={hooks}", "-c", "core.fsmonitor=false",
               "-c", "core.symlinks=false", "-c", "protocol.file.allow=never"]
    if folder is not None:
        command.extend(["-C", str(folder)])
    command.extend(arguments)
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240, check=False)
    if result.returncode:
        raise RuntimeError(f"Git {arguments[0]} failed: " + result.stderr[-1000:])
    return result.stdout.strip()


def inside(path, root):
    resolved = path.resolve()
    if not resolved.is_relative_to(root) or resolved == root:
        raise ValueError("Source path leaves the intended root")
    return resolved


def source_record(root, entry):
    repo, commit = entry["repository"], entry["commit"]
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo) or not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("Invalid source lock identity")
    url = "https://github.com/" + repo + ".git"
    existing = entry.get("existing_folder")
    target = inside(root / ".sources" / repo.replace("/", "_"), root)
    kept = False
    if existing:
        if not re.fullmatch(r"[\w.-]+", existing) or existing in {".", ".."}:
            raise ValueError("Invalid existing folder")
        original = inside(root / existing, root)
        if original.is_dir():
            target, kept = original, True
    created = False
    if target.exists():
        origin = git(target, "remote", "get-url", "origin")
        if origin.removesuffix(".git").casefold() != url.removesuffix(".git").casefold():
            raise ValueError("Existing folder has a different origin; unchanged")
    else:
        target.mkdir(parents=True, exist_ok=False)
        git(None, "init", "--quiet", str(target))
        git(target, "remote", "add", "origin", url)
        git(target, "fetch", "--quiet", "--depth", "1", "--filter=blob:none", "origin", commit)
        git(target, "checkout", "--quiet", "--detach", commit)
        created = True
    actual = git(target, "rev-parse", "HEAD")
    if not kept and actual != commit:
        raise ValueError("Existing source is at a different commit; unchanged")
    return {"repository": repo, "path": target.relative_to(root).as_posix(), "locked_commit": commit,
            "actual_commit": actual, "status": "added" if created else "existing-kept" if kept else "already-present",
            "matches_lock": actual == commit}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PACKAGE)
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    if not root.is_dir():
        raise SystemExit("Root must be an existing directory")
    entries = json.loads((PACKAGE / "catalog" / "sources.lock.json").read_text(encoding="utf-8"))["sources"]
    if args.repo:
        allowed = {e["repository"] for e in entries}
        if set(args.repo) - allowed:
            raise SystemExit("Requested repository is not in sources.lock.json")
        entries = [e for e in entries if e["repository"] in args.repo]
    if args.plan:
        for entry in entries:
            print(f'{entry["mode"]}: {entry["repository"]} @ {entry["commit"][:12]}')
        return
    receipt = root / "catalog" / "source-receipt.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    prior = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else {"sources": []}
    records = {r["repository"]: r for r in prior["sources"]}
    failures = []
    for entry in entries:
        repo = entry["repository"]
        print(f"Fetching {repo} ...", flush=True)
        try:
            record = source_record(root, entry)
            records[repo] = record
            print(f'{record["status"]}: {repo} ({record["actual_commit"][:12]})', flush=True)
        except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            failures.append({"repository": repo, "error": str(exc)})
            print(f"FAILED: {repo}: {type(exc).__name__}", flush=True)
        payload = {"checked_at": datetime.now(timezone.utc).isoformat(), "sources": list(records.values()), "failures": failures}
        temp = receipt.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(receipt)
    print(f"Complete: {len(entries) - len(failures)} sources, {len(failures)} failures", flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
