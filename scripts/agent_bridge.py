"""Read-only routing and selective project-scoped skill installation."""

import argparse
import hashlib
import importlib.util
import json
import platform as host_platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = {"codex": ".agents", "claude": ".claude"}
OPERATIONAL_FIELDS = {"hooks", "context", "agent", "shell", "disable-model-invocation", "user-invocable"}


class BridgeError(Exception):
    pass


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def blob_matches(raw, expected):
    for value in (raw, raw.replace(b"\r\n", b"\n")):
        blob = b"blob " + str(len(value)).encode() + b"\0" + value
        if hashlib.sha1(blob, usedforsecurity=False).hexdigest() == expected:
            return True
    return False


def inside(path, root):
    resolved = path.resolve()
    if resolved == root or not resolved.is_relative_to(root):
        raise BridgeError("Path leaves the authorized project or catalog")
    return resolved


def git(folder, *arguments):
    result = subprocess.run(["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null",
                             "-C", str(folder), *arguments], capture_output=True, timeout=30, check=False)
    if result.returncode:
        raise BridgeError("Read-only Git identity check failed; source unchanged")
    return result.stdout


class Catalog:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve(strict=True)
        self.data = read_json(self.root / "catalog/repositories.json")
        self.skills = read_json(self.root / "catalog/skills.json")["skills"]
        self.sources = read_json(self.root / "catalog/sources.lock.json")["sources"]
        self.notes = read_json(self.root / "catalog/skill-review-notes.json")
        self.profiles = read_json(self.root / "catalog/compatibility-profiles.json")

    def select(self, repository, name):
        matches = [s for s in self.skills if s["repository"] == repository and name in {s["name"], s.get("declared_name"), s["id"]}]
        if len(matches) != 1:
            raise BridgeError("Skill not found or selector is ambiguous; choose its exact id from search")
        return matches[0]

    def source(self, skill):
        entry = next((s for s in self.sources if s["repository"] == skill["repository"]), None)
        if not entry or entry["commit"] != skill["source_commit"]:
            raise BridgeError("Skill commit is not in the source lock")
        candidates = []
        if entry.get("existing_folder"):
            candidates.append(inside(self.root / entry["existing_folder"], self.root))
        candidates.append(inside(self.root / ".sources" / skill["repository"].replace("/", "_"), self.root))
        source = next((p for p in candidates if (p / skill["path"]).is_file()), None)
        if source is None:
            return None
        actual = git(source, "rev-parse", "HEAD").decode().strip()
        if actual != entry["commit"]:
            raise BridgeError("Local source commit differs from the lock; source unchanged")
        raw_path = source / skill["path"]
        if any(p.is_symlink() for p in [raw_path, *raw_path.parents] if p.is_relative_to(source)):
            raise BridgeError("Symlinked skill sources cannot be installed")
        path = inside(raw_path, source)
        if not blob_matches(path.read_bytes(), skill["blob_sha"]):
            raise BridgeError("Selected SKILL.md does not match its verified blob")
        return source

    def blocked_reason(self, skill):
        for item in self.notes["blocked_for_activation"]:
            if item["repository"] == skill["repository"] and item["path"] == skill["path"]:
                return item["reason"]
        return skill.get("activation_reason") if skill.get("activation_policy") == "blocked" else None

    def prerequisites(self, skill):
        profile = self.profiles["skills"].get(skill["name"])
        modules, executables = {}, {}
        for name in (profile or {}).get("modules", []):
            if not re.fullmatch(r"[A-Za-z_]\w*", name):
                raise BridgeError("Invalid module in prerequisite profile")
            modules[name] = importlib.util.find_spec(name) is not None
        for name in (profile or {}).get("executables", []):
            executables[name] = shutil.which(name) is not None
        return {"profile_coverage": profile["coverage"] if profile else "manual environment review required",
                "python_executable": sys.executable, "python_version": host_platform.python_version(),
                "modules": modules, "executables": executables,
                "services": (profile or {}).get("services", []) + self.profiles["repository_services"].get(skill["repository"], []),
                "missing": [k for k, value in {**modules, **executables}.items() if not value],
                "packages_installed_by_tool": False}

    def inspect(self, skill, target="both", show_content=False):
        reason = self.blocked_reason(skill)
        result = {"skill_id": skill["id"], "name": skill.get("declared_name", skill["name"]),
                  "repository": skill["repository"], "commit": skill["source_commit"], "url": skill["url"],
                  "blocked": bool(reason), "block_reason": reason, "available_locally": False,
                  "repository_license": skill["repository_license"], "prerequisites": self.prerequisites(skill),
                  "platform": target, "portability_issues": [], "functional_tested": False}
        source = self.source(skill)
        if source is None:
            result["next_step"] = f'python scripts/sync_sources.py --root . --repo {skill["repository"]}'
            result["installable"] = False
            return result
        result["available_locally"] = True
        md = inside(source / skill["path"], source)
        text = md.read_text(encoding="utf-8")
        front = text.split("---", 2)[1] if text.startswith("---") else ""
        keys = set(re.findall(r"^([\w-]+):", front, re.M))
        issues = []
        if "hooks" in keys or re.search(r"^\s*!`", text, re.M):
            issues.append("activation-time shell/hooks require manual adaptation")
        if target in {"codex", "both"} and re.search(r"\$\{CLAUDE_|\$ARGUMENTS", text):
            issues.append("Claude argument/path substitutions require manual Codex adaptation")
        if keys & {"context", "agent"}:
            issues.append("automatic subagent execution requires manual adaptation")
        if target in {"codex", "both"} and keys & OPERATIONAL_FIELDS:
            issues.append("Claude-specific operational frontmatter: " + ", ".join(sorted(keys & OPERATIONAL_FIELDS)))
        for reference in re.findall(r"\]\(([^)\s]+)\)", text):
            if "://" in reference or reference.startswith("#"):
                continue
            referenced = (md.parent / reference.split("#")[0]).resolve()
            if not referenced.is_relative_to(md.parent):
                issues.append("relative supporting-file reference leaves the skill directory")
                break
        for path in md.parent.rglob("*"):
            if path.name in {".mcp.json", "hooks.json"} or any(p in {".claude-plugin", ".codex-plugin"} for p in path.relative_to(md.parent).parts):
                issues.append("embedded plugin/hook configuration requires manual adaptation")
                break
        result["portability_issues"] = sorted(set(issues))
        result["frontmatter_keys"] = sorted(keys)
        result["installable"] = not reason and not issues
        result["license_notices"] = [p.name for p in md.parent.iterdir() if p.is_file() and re.match(r"(?i)license|copying|notice", p.name)]
        result["source_review"] = next((n for n in self.notes["notes"] if n["repository"] == skill["repository"]), None)
        if show_content:
            result["skill_content_untrusted"] = text
        return result

    def payload(self, skill):
        source = self.source(skill)
        if source is None:
            raise BridgeError("Source is not downloaded; run its explicit sync command first")
        skill_dir = inside(source / skill["path"], source).parent
        tracked = {}
        for record in git(source, "ls-tree", "-r", "-z", "HEAD").split(b"\0"):
            if not record:
                continue
            meta, raw_path = record.split(b"\t", 1)
            mode, kind, digest = meta.decode().split()
            tracked[raw_path.decode("utf-8")] = (mode, kind, digest)
        files = {}

        def add(path, destination):
            if path.is_symlink() or not path.resolve().is_relative_to(source):
                raise BridgeError("Symlink or external source file cannot be installed")
            relative = path.relative_to(source).as_posix()
            item = tracked.get(relative)
            if not item or item[0] not in {"100644", "100755"} or item[1] != "blob":
                raise BridgeError("Untracked or unsupported source file: " + relative)
            raw = path.read_bytes()
            if not blob_matches(raw, item[2]):
                raise BridgeError("Modified source supporting file: " + relative)
            files[destination] = raw

        for path in sorted(skill_dir.rglob("*")):
            if path.is_file():
                add(path, path.relative_to(skill_dir).as_posix())
        parent = skill_dir.parent
        while parent.is_relative_to(source):
            for path in parent.iterdir():
                if path.is_file() and re.match(r"(?i)^(license|copying|notice|third.party.notices)(\.|$)", path.name):
                    add(path, ".upstream-notices/" + path.relative_to(source).as_posix())
            if parent == source:
                break
            parent = parent.parent
        expected = {p for p in tracked if p.startswith(skill_dir.relative_to(source).as_posix() + "/")}
        present = {p.relative_to(source).as_posix() for p in skill_dir.rglob("*") if p.is_file()}
        if expected != present:
            raise BridgeError("Source skill directory has missing or extra files")
        return files

    def search(self, query="", category=None, limit=5, all_skills=False):
        categories = self.data["categories"]
        if category:
            categories = [c for c in categories if c["id"] == category]
            if not categories:
                raise BridgeError("Unknown category")
        terms = query.casefold().split()
        repo_keys = {r for c in categories for r in c["repositories"]}
        selected = {s for c in categories for s in c["skills"]} if category else {s["id"] for s in read_json(self.root / "catalog/selected-skills.json")["skills"]}
        repos = []
        for key in repo_keys:
            r = self.data["repositories"][key]
            haystack = " ".join([key, r["description"] or "", *r["topics"]]).casefold()
            if not terms or all(t in haystack for t in terms):
                repos.append({"repository": key, "url": r["url"], "stars": r["stars"], "score": r["score"], "checked_at": r["checked_at"]})
        skills = []
        for s in self.skills:
            haystack = " ".join([s["name"], s.get("declared_name", ""), s["repository"], s["path"]]).casefold()
            if (s["id"] in selected or all_skills) and (not terms or all(t in haystack for t in terms)):
                skills.append({"id": s["id"], "name": s.get("declared_name", s["name"]), "url": s["url"],
                               "commit": s["source_commit"], "blocked": bool(self.blocked_reason(s))})
        return {"categories": [c["id"] for c in categories], "repositories": sorted(repos, key=lambda r: r["score"], reverse=True)[:limit],
                "skills": skills[:limit], "inventory_note": "Historical inventory is not evidence of installation on this computer."}


def destination(project, target, name):
    if target not in PLATFORMS or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        raise BridgeError("Invalid platform or skill name")
    project = project.resolve(strict=True)
    return inside(project / PLATFORMS[target] / "skills" / name, project)


def write_bundle(project, target, name, files, origin, apply):
    dest = destination(project, target, name)
    digests = {k: sha256(v) for k, v in sorted(files.items())}
    record = {**origin, "files": digests}
    manifest = (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode()
    if dest.exists():
        existing = dest / ".INSTALLED_FROM.json"
        if not existing.is_file() or read_json(existing) != record:
            raise BridgeError("Destination already exists and is not the identical managed installation; unchanged")
        actual = {p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file() and p.name != ".INSTALLED_FROM.json"}
        if actual != set(files) or any(sha256((dest / p).read_bytes()) != digest for p, digest in digests.items()):
            raise BridgeError("Managed destination was modified; unchanged")
        return {"platform": target, "destination": str(dest), "status": "already-installed", "files": len(files)}
    if not apply:
        return {"platform": target, "destination": str(dest), "status": "planned", "files": len(files)}
    dest.parent.mkdir(parents=True, exist_ok=True)
    stage = inside(Path(tempfile.mkdtemp(prefix=".refs-stage-", dir=dest.parent)), project.resolve())
    try:
        for relative, raw in files.items():
            path = inside(stage / relative, stage)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        (stage / ".INSTALLED_FROM.json").write_bytes(manifest)
        stage.rename(dest)
    finally:
        if stage.exists():
            inside(stage, project.resolve())
            shutil.rmtree(stage)
    return {"platform": target, "destination": str(dest), "status": "installed", "files": len(files)}


def targets(value):
    return list(PLATFORMS) if value == "both" else [value]


def router_files(root, project):
    canonical = root / "skills/refs-catalog"
    files = {p.relative_to(canonical).as_posix(): p.read_bytes() for p in canonical.rglob("*")
             if p.is_file() and "__pycache__" not in p.parts}
    if project.resolve() != root:
        files["references/catalog-location.json"] = (json.dumps({"catalog_root": str(root)}, indent=2) + "\n").encode()
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("categories")
    sub.add_parser("doctor")
    find = sub.add_parser("search")
    find.add_argument("--query", default="")
    find.add_argument("--category")
    find.add_argument("--all-skills", action="store_true")
    find.add_argument("--limit", type=int, default=5, choices=range(1, 21))
    for command in ("inspect", "plan", "install"):
        cmd = sub.add_parser(command)
        cmd.add_argument("--repository", required=True)
        cmd.add_argument("--skill", required=True)
        cmd.add_argument("--platform", choices=["codex", "claude", "both"], default="both")
        if command == "inspect":
            cmd.add_argument("--show-content", action="store_true")
        else:
            cmd.add_argument("--project", type=Path, required=True)
            if command == "install":
                cmd.add_argument("--apply", action="store_true")
    router = sub.add_parser("install-router")
    router.add_argument("--project", type=Path, required=True)
    router.add_argument("--platform", choices=["codex", "claude", "both"], default="both")
    router.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        catalog = Catalog()
        if args.command == "categories":
            result = [{"id": c["id"], "name": c["name"]} for c in catalog.data["categories"]]
        elif args.command == "search":
            result = catalog.search(args.query, args.category, args.limit, args.all_skills)
        elif args.command == "doctor":
            result = {"python": host_platform.python_version(), "python_supported": sys.version_info >= (3, 10),
                      "git_available": shutil.which("git") is not None,
                      "claude_cli_available": shutil.which("claude") is not None,
                      "codex_cli_available": shutil.which("codex") is not None,
                      "catalog_valid_json": True, "categories": len(catalog.data["categories"]),
                      "global_configuration_changed": False, "upstream_skills_functionally_tested": False}
        elif args.command == "install-router":
            project = args.project.resolve(strict=True)
            files = router_files(catalog.root, project)
            origin = {"type": "claude-refs-router", "version": "1.0.0"}
            # Preflight every target before the first write.
            planned = [write_bundle(project, t, "refs-catalog", files, origin, False) for t in targets(args.platform)]
            result = [write_bundle(project, t, "refs-catalog", files, origin, args.apply) for t in targets(args.platform)] if args.apply else planned
        else:
            skill = catalog.select(args.repository, args.skill)
            result = catalog.inspect(skill, args.platform, getattr(args, "show_content", False))
            if args.command in {"plan", "install"}:
                if not result["installable"]:
                    raise BridgeError("Skill cannot be installed: " + (result["block_reason"] or "; ".join(result["portability_issues"]) or "source missing"))
                files = catalog.payload(skill)
                project = args.project.resolve(strict=True)
                name = result["name"]
                origin = {"type": "upstream-skill", "skill_id": skill["id"], "repository": skill["repository"],
                          "commit": skill["source_commit"], "url": skill["url"], "repository_license": skill["repository_license"]}
                planned = [write_bundle(project, t, name, files, origin, False) for t in targets(args.platform)]
                result["installation"] = [write_bundle(project, t, name, files, origin, True) for t in targets(args.platform)] if args.command == "install" and args.apply else planned
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (BridgeError, OSError, ValueError, StopIteration, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
