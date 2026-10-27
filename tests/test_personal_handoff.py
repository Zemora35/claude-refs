"""Personal entrypoint project binding; no personal installation or model calls."""

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("handoff_entry", ROOT / "skills/research-to-claude/scripts/handoff_entry.py")
ENTRY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENTRY)


class PersonalHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="personal-handoff-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.first = self.root / "first"
        self.second = self.root / "second"
        self.projectless = self.root / "chat-folder"
        for path in (self.first, self.second, self.projectless):
            path.mkdir()
        for path in (self.first, self.second):
            subprocess.run(["git", "init", "--quiet", str(path)], check=True, capture_output=True)

    def test_another_project_is_rejected_before_dispatch(self):
        with patch.object(ENTRY.Path, "cwd", return_value=self.first), patch.object(ENTRY, "toolkit_root") as toolkit:
            with self.assertRaises(SystemExit) as error:
                ENTRY.main(["run", "--bundle", "unrelated-task", "--expected-project", str(self.second), "--start"])
        self.assertEqual(error.exception.code, 2)
        toolkit.assert_not_called()

    def test_projectless_chat_never_falls_back_to_a_saved_project(self):
        state = ENTRY.active_context(self.projectless)
        self.assertIsNone(state["project_root"])
        with self.assertRaisesRegex(ENTRY.ContextError, "no Git project context"):
            ENTRY.check_project(self.first, self.projectless)

    def test_matching_active_project_is_forwarded_without_changing_it(self):
        original_run = subprocess.run
        delegated = []

        def local_or_capture(command, **kwargs):
            if command[0] == "git":
                return original_run(command, **kwargs)
            delegated.append(command)
            return SimpleNamespace(returncode=0)

        with patch.object(ENTRY.Path, "cwd", return_value=self.first), patch.object(ENTRY, "toolkit_root", return_value=ROOT), patch.object(ENTRY.subprocess, "run", side_effect=local_or_capture):
            with self.assertRaises(SystemExit) as result:
                ENTRY.main(["run", "--bundle", "this-chats-task", "--expected-project", str(self.first), "--start"])
        self.assertEqual(result.exception.code, 0)
        self.assertEqual(len(delegated), 1)
        self.assertIn(str(self.first), delegated[0])
        self.assertNotIn(str(self.second), delegated[0])
