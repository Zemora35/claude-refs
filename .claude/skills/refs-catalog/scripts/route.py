"""Locate the Claude Refs catalog and run its read-only agent commands."""

import json
import os
import subprocess
import sys
from pathlib import Path


def locate():
    skill = Path(__file__).resolve().parents[1]
    config = skill / "references" / "catalog-location.json"
    roots = []
    if os.environ.get("CLAUDE_REFS_ROOT"):
        roots.append(Path(os.environ["CLAUDE_REFS_ROOT"]))
    if config.is_file():
        roots.append(Path(json.loads(config.read_text(encoding="utf-8"))["catalog_root"]))
    roots.extend(skill.parents)
    for root in roots:
        if (root / "catalog" / "repositories.json").is_file() and (root / "scripts" / "agent_bridge.py").is_file():
            return root.resolve()
    raise SystemExit("Catalog checkout not found. Set CLAUDE_REFS_ROOT or reinstall the router from its checkout.")


def main():
    arguments = sys.argv[1:]
    if not arguments or arguments[0] not in {"categories", "search", "inspect", "doctor"}:
        raise SystemExit("Read-only commands: categories, search, inspect, doctor")
    root = locate()
    result = subprocess.run([sys.executable, str(root / "scripts" / "agent_bridge.py"), *arguments], check=False)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
