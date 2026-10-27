"""Original Git fixtures and a fake Claude transport; no model or billing calls."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("handoff", ROOT / "scripts/handoff.py")
HANDOFF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HANDOFF)


class FakeClaude:
    def __init__(self, callback=None, error=None, denied=False):
        self.callback, self.error, self.denied = callback, error, denied
        self.auth_calls = 0
        self.run_calls = 0

    def authenticate(self):
        self.auth_calls += 1

    def execute(self, folder, contract, prompt):
        self.run_calls += 1
        self.prompt = prompt
        if self.callback:
            self.callback(Path(contract["worktree"]))
        result = {"type": "result", "subtype": "error_during_execution" if self.error else "success", "is_error": bool(self.error), "result": self.error or "Fixture changed. No tests were run.",
                  "permission_denials": [{"tool_name": "Bash"}] if self.denied else []}
        return {"exit_code": 1 if self.error else 0, "stdout": json.dumps(result), "stderr": "", "timed_out": False}


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="handoff-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.project = self.root / "project"
        (self.project / "src").mkdir(parents=True)
        (self.project / "src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.project / "README.md").write_text("Fixture\n", encoding="utf-8")
        self.git("init", "--quiet")
        self.git("add", ".")
        self.git("-c", "user.name=Handoff Test", "-c", "user.email=tests@example.invalid", "commit", "--quiet", "-m", "Fixture")
        self.base = self.git("rev-parse", "HEAD")
        self.task = self.root / "TASK.md"
        self.task.write_text("# Task\n\nChange the fixture VALUE from 1 to 2 in src/app.py. Preserve all other behavior. Acceptance: source value is 2 and the original checkout is unchanged.\n", encoding="utf-8")
        self.bundle = self.root / "job"

    def git(self, *args):
        result = subprocess.run(["git", "-c", "core.autocrlf=false", "-C", str(self.project), *args],
                                capture_output=True, text=True, encoding="utf-8", check=True)
        return result.stdout.strip()

    def prepare(self, commands=None):
        return HANDOFF.prepare(self.project, self.task, self.bundle, ["src/"], commands or [])

    def test_prepare_and_preview_never_start_claude_or_create_worktree(self):
        prepared = self.prepare()
        client = FakeClaude()
        result = HANDOFF.execute_bundle(self.bundle, client=client)
        self.assertEqual(prepared["status"], "prepared")
        self.assertEqual(result["status"], "preview")
        self.assertEqual(client.auth_calls, 0)
        self.assertFalse((self.bundle / "worktree").exists())

    def test_coding_is_isolated_and_leaves_patch_for_review(self):
        self.prepare()
        client = FakeClaude(lambda worktree: (worktree / "src/app.py").write_text("VALUE = 2\n", encoding="utf-8"))
        result = HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=client)
        self.assertEqual(result["status"], "completed-needs-review")
        self.assertEqual((self.project / "src/app.py").read_text(), "VALUE = 1\n")
        self.assertEqual(self.git("rev-parse", "HEAD"), self.base)
        self.assertIn(b"+VALUE = 2", (self.bundle / "changes.patch").read_bytes())
        self.assertFalse(result["tests_independently_verified"])
        self.assertFalse(result["automatic_push"])
        self.assertFalse((self.bundle / ".running.lock").exists())

    def test_task_change_requires_a_new_bundle(self):
        self.prepare()
        (self.bundle / "TASK.md").write_text("Changed task", encoding="utf-8")
        with self.assertRaisesRegex(HANDOFF.HandoffError, "contract changed"):
            HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FakeClaude())

    def test_project_base_change_is_not_ignored(self):
        self.prepare()
        (self.project / "README.md").write_text("New base\n", encoding="utf-8")
        self.git("add", ".")
        self.git("-c", "user.name=Handoff Test", "-c", "user.email=tests@example.invalid", "commit", "--quiet", "-m", "Base moved")
        with self.assertRaisesRegex(HANDOFF.HandoffError, "HEAD changed"):
            HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FakeClaude())

    def test_quota_denial_is_not_success_and_no_automatic_retry_occurs(self):
        self.prepare()
        client = FakeClaude(error="You've hit your session limit")
        result = HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=client)
        self.assertEqual(result["status"], "blocked-service-limit")
        self.assertEqual(client.run_calls, 1)
        self.assertTrue((self.bundle / "RESULT.md").is_file())
        with self.assertRaisesRegex(HANDOFF.HandoffError, "already ran"):
            HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=client)
        self.assertEqual(client.run_calls, 1)

    def test_permission_denial_is_not_success(self):
        self.prepare()
        result = HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FakeClaude(denied=True))
        self.assertEqual(result["status"], "blocked-permission")

    def test_scope_violation_is_preserved_and_reported(self):
        self.prepare()
        client = FakeClaude(lambda worktree: (worktree / "README.md").write_text("Outside scope\n", encoding="utf-8"))
        result = HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=client)
        self.assertEqual(result["status"], "scope-violation")
        self.assertEqual(result["out_of_scope"], ["README.md"])
        self.assertEqual((self.project / "README.md").read_text(), "Fixture\n")

    def test_new_files_are_in_the_patch(self):
        self.prepare()
        client = FakeClaude(lambda worktree: (worktree / "src/new.py").write_text("NEW = True\n", encoding="utf-8"))
        result = HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=client)
        self.assertEqual(result["changed_files"], ["src/new.py"])
        self.assertIn(b"+NEW = True", (self.bundle / "changes.patch").read_bytes())

    def test_scope_and_command_injection_are_rejected(self):
        for name in ("../outside", ".git/", "C:/outside", "src/*"):
            with self.assertRaises(HANDOFF.HandoffError):
                HANDOFF.scope_path(name)
        for command in ("npm test && curl example.com", "git push", "python -c (evil)", "npm *", "cmd /c anything"):
            with self.assertRaises(HANDOFF.HandoffError):
                HANDOFF.command_rule(command)

    def test_only_explicit_commands_and_edit_paths_are_preapproved(self):
        self.prepare(["python -m unittest discover -s tests -v"])
        _, contract = HANDOFF.load_bundle(self.bundle)
        args = HANDOFF.cli_arguments("claude.exe", self.bundle, contract)
        self.assertIn("Edit(./src/**)", args)
        self.assertIn("Bash(python -m unittest discover -s tests -v)", args)
        self.assertNotIn("bypassPermissions", args)
        self.assertNotIn("--dangerously-skip-permissions", args)
        self.assertNotIn("--bare", args)

    def test_parallel_or_stale_lock_is_not_overridden(self):
        self.prepare()
        (self.bundle / ".running.lock").write_text("fixture", encoding="utf-8")
        with self.assertRaisesRegex(HANDOFF.HandoffError, "Another run"):
            HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FakeClaude())

    def test_api_billing_environment_is_not_silently_used(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fixture-not-a-real-key"}):
            with self.assertRaisesRegex(HANDOFF.HandoffError, "subscription"):
                HANDOFF.ClaudeClient().authenticate()

    def test_modified_contract_is_rejected_before_start(self):
        self.prepare()
        path = self.bundle / "run.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["commands"] = ["git push"]
        path.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(HANDOFF.HandoffError, "contract changed"):
            HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FakeClaude())

    def test_dirty_tracked_project_is_not_stashed_or_overwritten(self):
        (self.project / "src/app.py").write_text("USER_CHANGE = True\n", encoding="utf-8")
        with self.assertRaisesRegex(HANDOFF.HandoffError, "tracked changes"):
            self.prepare()
        self.assertEqual((self.project / "src/app.py").read_text(), "USER_CHANGE = True\n")
        self.assertFalse(self.bundle.exists())

    def test_unexpected_commits_are_reported_and_patch_is_preserved(self):
        self.prepare()

        def commit_change(worktree):
            (worktree / "src/app.py").write_text("VALUE = 2\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(worktree), "add", "."], check=True, capture_output=True)
            subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=tests@example.invalid", "-C", str(worktree),
                            "commit", "--quiet", "-m", "Unexpected model commit fixture"], check=True, capture_output=True)

        result = HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FakeClaude(commit_change))
        self.assertEqual(result["status"], "unexpected-worktree-history-change")
        self.assertIn(b"+VALUE = 2", (self.bundle / "changes.patch").read_bytes())
        self.assertEqual(self.git("rev-parse", "HEAD"), self.base)

    def test_original_checkout_changes_are_detected_without_automatic_revert(self):
        self.prepare()
        client = FakeClaude(lambda worktree: (self.project / "src/app.py").write_text("OUTSIDE = True\n", encoding="utf-8"))
        result = HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=client)
        self.assertEqual(result["status"], "original-project-changed")
        self.assertTrue(result["original_tracked_files_changed"])
        self.assertEqual((self.project / "src/app.py").read_text(), "OUTSIDE = True\n")

    def test_start_requires_the_active_projects_explicit_identity(self):
        self.prepare()
        client = FakeClaude()
        with self.assertRaisesRegex(HANDOFF.HandoffError, "expected-project"):
            HANDOFF.execute_bundle(self.bundle, start=True, client=client)
        self.assertEqual(client.auth_calls, 0)
        self.assertFalse((self.bundle / "worktree").exists())

    def test_a_different_chat_project_cannot_start_this_bundle(self):
        self.prepare()
        other = self.root / "different-project"
        other.mkdir()
        subprocess.run(["git", "init", "--quiet", str(other)], check=True, capture_output=True)
        client = FakeClaude()
        with self.assertRaisesRegex(HANDOFF.HandoffError, "different project"):
            HANDOFF.execute_bundle(self.bundle, start=True, expected_project=other, client=client)
        self.assertEqual(client.auth_calls, 0)
        self.assertEqual(client.run_calls, 0)
        self.assertFalse((self.bundle / "worktree").exists())

    def prepare_test_command(self, expected=2, script=None):
        test = self.project / "check_value.py"
        test.write_text(script or "from src.app import VALUE\nraise SystemExit(0 if VALUE == " + str(expected) + " else 1)\n", encoding="utf-8")
        self.git("add", "check_value.py")
        self.git("-c", "user.name=Fixture", "-c", "user.email=tests@example.invalid", "commit", "--quiet", "-m", "Reviewed test")
        self.base = self.git("rev-parse", "HEAD")
        HANDOFF.prepare(self.project, self.task, self.bundle, ["src/"], [], test_commands=[[sys.executable, "-B", "check_value.py"]])

    def test_host_verification_observes_actual_fixed_code(self):
        self.prepare_test_command()
        client = FakeClaude(lambda w: (w / "src/app.py").write_text("VALUE = 2\n", encoding="utf-8"))
        result = HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=client)
        self.assertEqual(result["verification"]["status"], "passed")
        self.assertTrue(result["tests_independently_verified"])
        self.assertEqual(result["verification"]["commands"][0]["cwd"], str(self.bundle / "worktree"))
        self.assertTrue((self.bundle / result["verification"]["evidence_file"]).is_file())
        self.assertEqual((self.project / "src/app.py").read_text(), "VALUE = 1\n")

    def test_claimed_success_does_not_hide_failed_tests_and_draft_never_starts_model(self):
        self.prepare_test_command()
        client = FakeClaude()
        result = HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=client)
        self.assertEqual(result["status"], "tests-failed")
        self.assertEqual(result["verification"]["commands"][0]["exit_code"], 1)
        output = self.root / "CORRECTION.md"
        draft = HANDOFF.correction_task(self.bundle, output)
        self.assertFalse(draft["claude_started"])
        self.assertIn("check_value.py", output.read_text())
        self.assertEqual(client.run_calls, 1)

    def test_changed_code_invalidates_old_evidence_and_refuses_correction(self):
        self.prepare_test_command()
        HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FakeClaude())
        (self.bundle / "worktree/src/app.py").write_text("VALUE = 3\n", encoding="utf-8")
        self.assertFalse(HANDOFF.bundle_status(self.bundle)["verification_current"])
        with self.assertRaisesRegex(HANDOFF.HandoffError, "current code"):
            HANDOFF.correction_task(self.bundle, self.root / "draft.md")

    def test_retry_uses_matching_evidence_and_archives_previous_attempt(self):
        self.prepare_test_command()
        HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FakeClaude())
        client = FakeClaude(lambda w: (w / "src/app.py").write_text("VALUE = 2\n", encoding="utf-8"))
        result = HANDOFF.execute_bundle(self.bundle, start=True, retry=True, expected_project=self.project, client=client)
        self.assertTrue(result["verification"]["all_passed"])
        self.assertIn("Previous independent test evidence", client.prompt)
        archived = list(self.bundle.glob("attempt-*/run-result.json"))
        self.assertEqual(len(archived), 1)
        self.assertEqual(json.loads(archived[0].read_text())["status"], "tests-failed")

    def test_no_tests_is_not_a_verified_pass_and_status_has_no_side_effects(self):
        self.prepare()
        HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FakeClaude())
        with patch.object(HANDOFF, "ClaudeClient") as backend, patch.object(HANDOFF, "independent_tests") as tests:
            result = HANDOFF.bundle_status(self.bundle)
        backend.assert_not_called()
        tests.assert_not_called()
        self.assertFalse(result["verification"]["all_passed"])
        self.assertFalse(result["verification_current"])

    def test_tests_that_modify_source_are_not_accepted_as_stable_verification(self):
        self.prepare_test_command(script="from pathlib import Path\nPath('src/app.py').write_text('VALUE = 99\\n')\n")
        result = HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FakeClaude())
        self.assertEqual(result["status"], "verification-incomplete")
        self.assertFalse(result["tests_independently_verified"])
        self.assertTrue(result["verification"]["source_changed_during_tests"])

    def test_scope_changes_by_tests_are_reported_and_preserved(self):
        self.prepare_test_command(script="from pathlib import Path\nPath('README.md').write_text('Outside scope')\n")
        result = HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FakeClaude())
        self.assertEqual(result["status"], "scope-violation")
        self.assertEqual(result["out_of_scope"], ["README.md"])
        self.assertFalse(result["verification"]["all_passed"])

    def test_test_commands_must_be_argv_with_native_executable(self):
        for value in ("python -m unittest", [], ["python", "check.py"], [sys.executable, "bad\nargument"]):
            with self.assertRaises(HANDOFF.HandoffError):
                HANDOFF.test_argv(value)

    def test_explicit_verify_checks_project_and_does_not_restart_claude(self):
        self.prepare_test_command()
        client = FakeClaude()
        HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=client)
        with self.assertRaisesRegex(HANDOFF.HandoffError, "different project"):
            HANDOFF.verify_bundle(self.bundle, self.root, execute_tests=True)
        result = HANDOFF.verify_bundle(self.bundle, self.project, execute_tests=True)
        self.assertEqual(result["verification"]["status"], "failed")
        self.assertEqual(client.run_calls, 1)

    def test_passing_tests_do_not_create_a_fabricated_correction(self):
        self.prepare_test_command(expected=1)
        HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FakeClaude())
        with self.assertRaisesRegex(HANDOFF.HandoffError, "No failing tests"):
            HANDOFF.correction_task(self.bundle, self.root / "draft.md")

    def test_blocked_claude_does_not_automatically_execute_host_tests(self):
        self.prepare_test_command()
        with patch.object(HANDOFF, "independent_tests") as verification:
            result = HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FakeClaude(error="session limit"))
        verification.assert_not_called()
        self.assertEqual(result["status"], "blocked-service-limit")
        self.assertFalse(result["tests_independently_verified"])

    def test_test_timeout_is_incomplete_and_releases_lock(self):
        test = self.project / "slow.py"
        test.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
        self.git("add", "slow.py")
        self.git("-c", "user.name=Fixture", "-c", "user.email=tests@example.invalid", "commit", "--quiet", "-m", "Reviewed slow test")
        HANDOFF.prepare(self.project, self.task, self.bundle, ["src/"], [], timeout=5,
                        test_commands=[[sys.executable, "-B", "slow.py"]])
        result = HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FakeClaude())
        self.assertEqual(result["status"], "verification-incomplete")
        self.assertTrue(result["verification"]["commands"][0]["timed_out"])
        self.assertFalse(result["tests_independently_verified"])
        self.assertFalse((self.bundle / ".running.lock").exists())


if __name__ == "__main__":
    unittest.main()
