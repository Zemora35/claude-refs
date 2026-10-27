"""Behavioral tests using an original local Git fixture; no model/network calls."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("agent_bridge", ROOT / "scripts/agent_bridge.py")
BRIDGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BRIDGE)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="refs-bridge-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root / ".sources/fixture_skills"
        self.directory = self.source / "skills/fixture-tool"
        self.directory.mkdir(parents=True)
        self.md = self.directory / "SKILL.md"
        self.md.write_text("---\nname: fixture-tool\ndescription: Test the local catalog fixture.\n---\nUse helper.py only when explicitly requested.\n", encoding="utf-8")
        (self.directory / "helper.py").write_text("raise RuntimeError('source helper must never run during installation')\n", encoding="utf-8")
        (self.source / "LICENSE").write_text("MIT fixture notice\n", encoding="utf-8")
        self.git("init", "--quiet")
        self.git("add", ".")
        self.git("-c", "user.name=Catalog Test", "-c", "user.email=tests@example.invalid", "commit", "--quiet", "-m", "Fixture")
        self.commit = self.git("rev-parse", "HEAD")
        self.blob = self.git("rev-parse", "HEAD:skills/fixture-tool/SKILL.md")
        self.skill = {"id": "fixture/skills:skills/fixture-tool/SKILL.md", "name": "fixture-tool", "declared_name": "fixture-tool",
                      "repository": "fixture/skills", "path": "skills/fixture-tool/SKILL.md", "source_commit": self.commit,
                      "blob_sha": self.blob, "url": "https://github.com/fixture/skills/blob/" + self.commit + "/skills/fixture-tool/SKILL.md",
                      "repository_license": "MIT", "activation_policy": "review-before-activation"}
        self.project = self.root / "consumer"
        self.project.mkdir()
        save(self.root / "catalog/repositories.json", {"categories": [{"id": "testing", "name": "Testing", "repositories": ["fixture/skills"], "skills": [self.skill["id"]]}],
                                                      "repositories": {"fixture/skills": {"description": "Fixture", "topics": [], "url": "https://github.com/fixture/skills", "stars": 1, "score": 1, "checked_at": "2026-10-27"}}})
        save(self.root / "catalog/skills.json", {"skills": [self.skill]})
        save(self.root / "catalog/selected-skills.json", {"skills": [self.skill]})
        save(self.root / "catalog/sources.lock.json", {"sources": [{"repository": "fixture/skills", "commit": self.commit}]})
        save(self.root / "catalog/skill-review-notes.json", {"notes": [], "blocked_for_activation": []})
        save(self.root / "catalog/compatibility-profiles.json", {"skills": {}, "repository_services": {}})
        self.catalog = BRIDGE.Catalog(self.root)

    def git(self, *args):
        result = subprocess.run(["git", "-c", "core.autocrlf=false", "-C", str(self.source), *args],
                                capture_output=True, check=True, text=True, encoding="utf-8")
        return result.stdout.strip()

    def test_plan_has_no_installation_side_effect(self):
        files = self.catalog.payload(self.skill)
        result = BRIDGE.write_bundle(self.project, "codex", "fixture-tool", files, {"type": "test"}, False)
        self.assertEqual(result["status"], "planned")
        self.assertFalse((self.project / ".agents").exists())
        self.assertIn(".upstream-notices/LICENSE", files)

    def test_install_both_preserves_files_and_is_idempotent(self):
        files = self.catalog.payload(self.skill)
        for target, folder in BRIDGE.PLATFORMS.items():
            result = BRIDGE.write_bundle(self.project, target, "fixture-tool", files, {"type": "test"}, True)
            self.assertEqual(result["status"], "installed")
            dest = self.project / folder / "skills/fixture-tool"
            self.assertEqual((dest / "SKILL.md").read_bytes(), self.md.read_bytes())
            self.assertTrue((dest / ".upstream-notices/LICENSE").is_file())
            self.assertEqual(BRIDGE.write_bundle(self.project, target, "fixture-tool", files, {"type": "test"}, True)["status"], "already-installed")

    def test_existing_unmanaged_skill_is_not_overwritten(self):
        dest = self.project / ".claude/skills/fixture-tool"
        dest.mkdir(parents=True)
        (dest / "SKILL.md").write_text("user content", encoding="utf-8")
        with self.assertRaisesRegex(BRIDGE.BridgeError, "Destination already exists"):
            BRIDGE.write_bundle(self.project, "claude", "fixture-tool", self.catalog.payload(self.skill), {}, True)
        self.assertEqual((dest / "SKILL.md").read_text(), "user content")

    def test_modified_supporting_code_is_rejected(self):
        (self.directory / "helper.py").write_text("modified", encoding="utf-8")
        with self.assertRaisesRegex(BRIDGE.BridgeError, "Modified source supporting file"):
            self.catalog.payload(self.skill)

    def test_untracked_file_is_rejected(self):
        (self.directory / "untracked.env").write_text("fixture", encoding="utf-8")
        with self.assertRaisesRegex(BRIDGE.BridgeError, "Untracked"):
            self.catalog.payload(self.skill)

    def test_missing_support_file_is_rejected(self):
        (self.directory / "helper.py").unlink()
        with self.assertRaisesRegex(BRIDGE.BridgeError, "missing or extra"):
            self.catalog.payload(self.skill)

    def test_modified_skill_is_rejected(self):
        self.md.write_text("modified", encoding="utf-8")
        with self.assertRaisesRegex(BRIDGE.BridgeError, "verified blob"):
            self.catalog.inspect(self.skill)

    def test_blocked_skill_cannot_reach_installer(self):
        self.catalog.notes["blocked_for_activation"] = [{"repository": "fixture/skills", "path": self.skill["path"], "reason": "fixture blocked"}]
        args = ["bridge", "install", "--repository", "fixture/skills", "--skill", "fixture-tool", "--project", str(self.project), "--apply"]
        with patch.object(BRIDGE, "Catalog", return_value=self.catalog), patch.object(sys, "argv", args):
            with self.assertRaises(SystemExit) as error:
                BRIDGE.main()
        self.assertEqual(error.exception.code, 2)
        self.assertFalse((self.project / ".agents").exists())

    def test_crlf_conversion_preserves_git_identity(self):
        self.md.write_bytes(self.md.read_bytes().replace(b"\n", b"\r\n"))
        self.assertTrue(self.catalog.inspect(self.skill)["available_locally"])

    def test_path_escape_and_unknown_platform_are_rejected(self):
        for name in ("../escape", "bad/name", "UpperCase"):
            with self.assertRaises(BRIDGE.BridgeError):
                BRIDGE.destination(self.project, "codex", name)
        with self.assertRaises(BRIDGE.BridgeError):
            BRIDGE.destination(self.project, "unsupported", "fixture-tool")

    def test_absent_source_does_not_claim_installation(self):
        self.catalog.sources[0]["existing_folder"] = "absent"
        self.skill["path"] = "skills/missing/SKILL.md"
        result = self.catalog.inspect(self.skill)
        self.assertFalse(result["available_locally"])
        self.assertFalse(result["installable"])
        self.assertIn("sync_sources", result["next_step"])

    def test_router_helper_rejects_mutating_subcommands(self):
        helper = ROOT / "skills/refs-catalog/scripts/route.py"
        result = subprocess.run([sys.executable, str(helper), "install", "--apply"], capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Read-only commands", result.stderr)

    def test_modified_destination_is_not_silently_replaced(self):
        files = self.catalog.payload(self.skill)
        BRIDGE.write_bundle(self.project, "codex", "fixture-tool", files, {"type": "test"}, True)
        destination = self.project / ".agents/skills/fixture-tool/SKILL.md"
        destination.write_text("user edit", encoding="utf-8")
        with self.assertRaisesRegex(BRIDGE.BridgeError, "destination was modified"):
            BRIDGE.write_bundle(self.project, "codex", "fixture-tool", files, {"type": "test"}, True)
        self.assertEqual(destination.read_text(), "user edit")

    def test_unknown_category_is_reported(self):
        with self.assertRaisesRegex(BRIDGE.BridgeError, "Unknown category"):
            self.catalog.search(category="not-a-category")

    def test_claude_activation_features_are_not_automatically_installed(self):
        self.md.write_text("---\nname: fixture-tool\ndescription: Fixture.\ncontext: fork\n---\n!`echo test`\n", encoding="utf-8")
        self.git("add", ".")
        self.git("-c", "user.name=Catalog Test", "-c", "user.email=tests@example.invalid", "commit", "--quiet", "-m", "Metadata fixture")
        self.skill["source_commit"] = self.git("rev-parse", "HEAD")
        self.skill["blob_sha"] = self.git("rev-parse", "HEAD:skills/fixture-tool/SKILL.md")
        self.catalog.sources[0]["commit"] = self.skill["source_commit"]
        for target in ("codex", "claude", "both"):
            result = self.catalog.inspect(self.skill, target)
            self.assertFalse(result["installable"])
            self.assertTrue(result["portability_issues"])

    def test_claude_arguments_are_reported_as_platform_specific(self):
        self.md.write_text("---\nname: fixture-tool\ndescription: Fixture.\n---\nAnalyze **$ARGUMENTS**.\n", encoding="utf-8")
        self.git("add", ".")
        self.git("-c", "user.name=Catalog Test", "-c", "user.email=tests@example.invalid", "commit", "--quiet", "-m", "Arguments fixture")
        self.skill["source_commit"] = self.git("rev-parse", "HEAD")
        self.skill["blob_sha"] = self.git("rev-parse", "HEAD:skills/fixture-tool/SKILL.md")
        self.catalog.sources[0]["commit"] = self.skill["source_commit"]
        self.assertTrue(self.catalog.inspect(self.skill, "claude")["installable"])
        self.assertFalse(self.catalog.inspect(self.skill, "codex")["installable"])


if __name__ == "__main__":
    unittest.main()
