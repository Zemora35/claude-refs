"""Verify actual process ownership without model calls or external programs."""

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from process_tree import ProcessTree  # noqa: E402


class ProcessTreeTests(unittest.TestCase):
    def test_normal_process_returns_actual_output(self):
        with ProcessTree([sys.executable, "-c", "print('owned process')"], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True) as tree:
            stdout, stderr = tree.process.communicate(timeout=10)
            self.assertEqual(tree.process.returncode, 0)
            self.assertEqual(stdout.strip(), "owned process")
            self.assertEqual(stderr, "")

    def test_stop_closes_descendant_inherited_pipes(self):
        program = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']); print('ready',flush=True); time.sleep(30)"
        with ProcessTree([sys.executable, "-c", program], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True) as tree:
            self.assertEqual(tree.process.stdout.readline().strip(), "ready")
            tree.stop()
            tree.process.communicate(timeout=5)
            self.assertIsNotNone(tree.process.returncode)


if __name__ == "__main__":
    unittest.main()
