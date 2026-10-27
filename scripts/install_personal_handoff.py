"""Install this original workflow in local user skill directories, without overwriting existing skills."""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--enable-research-default", action="store_true", help="Opt in to bounded Codex research for newly prepared personal tasks")
    args = parser.parse_args()
    source = ROOT / "skills/research-to-claude"
    if not (ROOT / "scripts/handoff.py").is_file() or not (source / "SKILL.md").is_file():
        raise SystemExit("Complete local toolkit checkout required")
    destinations = [Path.home() / ".agents/skills/research-to-claude", Path.home() / ".claude/skills/research-to-claude"]
    for destination in destinations:
        if destination.exists():
            raise SystemExit("Existing personal skill was left unchanged: " + str(destination))
    if not args.apply:
        print(json.dumps({"status": "planned", "destinations": [str(p) for p in destinations], "claude_started": False}, indent=2))
        return
    results = []
    for destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "installation.json"))
        references = destination / "references"
        references.mkdir(exist_ok=True)
        config = {"toolkit_root": str(ROOT), "python_executable": sys.executable, "version": "1.1.0",
                  "research_default_enabled": args.enable_research_default,
                  "project_selection": "active chat cwd and explicit expected project; no last-project fallback"}
        (references / "installation.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        hashes = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts}
        (destination / ".INSTALLED_FROM.json").write_text(json.dumps({"type": "original-claude-refs-personal-handoff", "files": hashes}, indent=2) + "\n", encoding="utf-8")
        results.append({"destination": str(destination), "status": "installed", "claude_started": False})
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
