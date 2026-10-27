"""Personal skill entrypoint: bind handoff commands to the active process cwd."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


class ContextError(Exception):
    pass


def personal_settings():
    path = Path(__file__).resolve().parents[1] / "references/installation.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def toolkit_root():
    skill = Path(__file__).resolve().parents[1]
    installed = skill / "references/installation.json"
    if installed.is_file():
        root = Path(json.loads(installed.read_text(encoding="utf-8"))["toolkit_root"]).resolve(strict=True)
        if not (root / "scripts/handoff.py").is_file():
            raise ContextError("Registered toolkit is unavailable; reinstall this personal skill")
        return root
    for root in skill.parents:
        if (root / "scripts/handoff.py").is_file() and (root / "catalog/repositories.json").is_file():
            return root
    raise ContextError("Toolkit checkout not found; install this skill from the local Claude Refs toolkit")


def active_context(cwd=None):
    cwd = Path(cwd or Path.cwd()).resolve(strict=True)
    result = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(cwd), "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15, check=False)
    if result.returncode:
        return {"cwd": str(cwd), "project_root": None, "status": "project-required", "claude_started": False}
    return {"cwd": str(cwd), "project_root": str(Path(result.stdout.strip()).resolve()), "status": "git-context-found", "claude_started": False}


def check_project(expected, cwd=None):
    context = active_context(cwd)
    if context["project_root"] is None:
        raise ContextError("This chat has no Git project context; ask the user for the project folder")
    if expected is None or Path(expected).resolve(strict=True) != Path(context["project_root"]):
        raise ContextError("Requested project differs from the active working directory's Git project; no task was forwarded")
    return context


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] not in {"context", "prepare", "run", "launch", "wait", "status", "verify", "draft-correction"}:
        raise SystemExit("Commands: context, prepare, run, launch, wait, status, verify, draft-correction")
    try:
        if arguments[0] == "context":
            context = active_context()
            context["toolkit_available"] = (toolkit_root() / "scripts/handoff.py").is_file()
            print(json.dumps(context, ensure_ascii=False, indent=2))
            return
        selector = argparse.ArgumentParser(add_help=False)
        selector.add_argument("--project")
        selector.add_argument("--expected-project")
        chosen, _ = selector.parse_known_args(arguments[1:])
        check_project(chosen.project if arguments[0] == "prepare" else chosen.expected_project)
        if arguments[0] == "prepare" and not {"--enable-research", "--disable-research"}.intersection(arguments) and personal_settings().get("research_default_enabled") is True:
            arguments.append("--enable-research")
        root = toolkit_root()
        script = "scripts/handoff_job.py" if arguments[0] in {"launch", "wait"} else "scripts/handoff.py"
        if arguments[0] == "launch":
            arguments[0] = "start"
        result = subprocess.run([sys.executable, "-B", str(root / script), *arguments], check=False)
        raise SystemExit(result.returncode)
    except (ContextError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"error": str(exc), "claude_started": False}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
