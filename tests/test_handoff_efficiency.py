"""Scope budgets, test phases and real local background-worker fixtures; no model calls."""

import importlib.util
import json
import os
import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import test_handoff as fixtures

FakeClaude, HANDOFF, ROOT = fixtures.FakeClaude, fixtures.HANDOFF, fixtures.ROOT


class EfficientHandoffTests(unittest.TestCase):
    setUp = fixtures.HandoffTests.setUp
    git = fixtures.HandoffTests.git

    def add_test(self, name, body):
        (self.project / name).write_text(body, encoding="utf-8")
        self.git("add", name)
        self.git("-c", "user.name=Fixture", "-c", "user.email=tests@example.invalid", "commit", "--quiet", "-m", name)
        return [sys.executable, "-B", name]

    def prepare_phases(self, target_exit=0):
        target = self.add_test("target.py", "from pathlib import Path\np=Path('phase-order');p.write_text((p.read_text() if p.exists() else '')+'target\\n')\nraise SystemExit("+str(target_exit)+")\n")
        final = self.add_test("final.py", "from pathlib import Path\np=Path('phase-order');p.write_text(p.read_text()+'final\\n')\n")
        # Test markers are ignored artefacts, not source edits.
        (self.project / ".gitignore").write_text("phase-order\n", encoding="utf-8")
        self.git("add", ".gitignore")
        self.git("-c", "user.name=Fixture", "-c", "user.email=tests@example.invalid", "commit", "--quiet", "-m", "Ignore test evidence")
        HANDOFF.prepare(self.project,self.task,self.bundle,["src/"],[],test_commands=[final],
                        issue_groups=["fixture value"],target_test_commands=[target])
        return target,final

    def test_scope_rejects_third_group_and_oversized_task(self):
        with self.assertRaisesRegex(HANDOFF.HandoffError,"one or two"):
            HANDOFF.prepare(self.project,self.task,self.bundle,["src/"],[],issue_groups=["one","two","three"])
        self.assertFalse(self.bundle.exists())
        self.task.write_text("x"*(HANDOFF.MAX_TASK_BYTES+1),encoding="utf-8")
        with self.assertRaisesRegex(HANDOFF.HandoffError,"12000"):
            HANDOFF.prepare(self.project,self.task,self.bundle,["src/"],[])
        self.assertFalse(self.bundle.exists())

    def test_explicit_final_command_cannot_be_granted_to_claude(self):
        argv=self.add_test("check.py","pass\n")
        with self.assertRaisesRegex(HANDOFF.HandoffError,"host verification"):
            HANDOFF.prepare(self.project,self.task,self.bundle,["src/"],[HANDOFF.argv_command(argv)],test_commands=[argv])

    def test_only_targeted_command_is_automatically_granted(self):
        target,final=self.prepare_phases()
        _,record=HANDOFF.load_bundle(self.bundle)
        args=HANDOFF.cli_arguments("claude.exe",self.bundle,record)
        self.assertIn(HANDOFF.command_rule(HANDOFF.argv_command(target)),args)
        self.assertNotIn(HANDOFF.command_rule(HANDOFF.argv_command(final)),args)
        prompt=HANDOFF.make_prompt(self.bundle,record)
        self.assertIn("Do not run the full regression suite",prompt)

    def test_targeted_runs_before_single_final_suite(self):
        self.prepare_phases()
        result=HANDOFF.execute_bundle(self.bundle,start=True,expected_project=self.project,client=FakeClaude())
        self.assertEqual((self.bundle/"worktree/phase-order").read_text(),"target\nfinal\n")
        self.assertEqual([r["phase"] for r in result["verification"]["commands"]],["targeted","final"])
        self.assertTrue(result["verification"]["all_passed"])

    def test_failing_target_skips_final_without_claiming_verified_suite(self):
        self.prepare_phases(1)
        result=HANDOFF.execute_bundle(self.bundle,start=True,expected_project=self.project,client=FakeClaude())
        self.assertEqual((self.bundle/"worktree/phase-order").read_text(),"target\n")
        self.assertEqual(result["status"],"tests-failed")
        self.assertTrue(result["verification"]["targeted_tests_verified"])
        self.assertTrue(result["verification"]["final_suite_skipped"])
        self.assertFalse(result["tests_independently_verified"])
        draft=HANDOFF.correction_task(self.bundle,self.root/"correction.md")
        self.assertFalse(draft["claude_started"])

    def test_raw_logs_preserved_but_model_summary_bounded(self):
        value={"status":"failed","evidence_file":"verification.json","commands":[{"argv":[sys.executable,"check.py"],"exit_code":1,"stdout":"irrelevant\n"*15000,"stderr":"AssertionError: actual failure\n"}]}
        small=HANDOFF.compact_verification(value)
        self.assertLess(len(json.dumps(small)),2000)
        self.assertIn("actual failure",small["commands"][0]["observed_excerpt"])
        self.assertEqual(len(value["commands"][0]["stdout"]),165000)

    def test_target_source_mutation_skips_final_and_invalidates_evidence(self):
        target=self.add_test("mutate.py","from pathlib import Path\nPath('src/app.py').write_text('VALUE = 99\\n')\n")
        final=self.add_test("final.py","raise RuntimeError('final must not run')\n")
        HANDOFF.prepare(self.project,self.task,self.bundle,["src/"],[],target_test_commands=[target],test_commands=[final])
        result=HANDOFF.execute_bundle(self.bundle,start=True,expected_project=self.project,client=FakeClaude())
        self.assertTrue(result["verification"]["source_changed_during_tests"])
        self.assertTrue(result["verification"]["final_suite_skipped"])
        self.assertFalse(result["tests_independently_verified"])
        self.assertEqual(len(result["verification"]["commands"]),1)

    def test_legacy_sealed_bundle_remains_loadable(self):
        HANDOFF.prepare(self.project,self.task,self.bundle,["src/"],[])
        record=json.loads((self.bundle/"run.json").read_text())
        record.pop("contract_sha256")
        for name in ("issue_groups","target_test_commands","test_policy"):
            record.pop(name)
        HANDOFF.save(self.bundle/"run.json",{**record,"contract_sha256":HANDOFF.digest(record)})
        _,loaded=HANDOFF.load_bundle(self.bundle)
        self.assertNotIn("issue_groups",loaded)

    def test_running_worker_does_not_report_previous_test_evidence_as_current(self):
        self.prepare_phases()
        HANDOFF.execute_bundle(self.bundle,start=True,expected_project=self.project,client=FakeClaude())
        self.assertTrue(HANDOFF.bundle_status(self.bundle)["verification_current"])
        HANDOFF.save(self.bundle/"job.json",{"status":"running","job_id":"fixture"})
        status=HANDOFF.bundle_status(self.bundle)
        self.assertEqual(status["status"],"running")
        self.assertFalse(status["verification_current"])
        with self.assertRaisesRegex(HANDOFF.HandoffError,"current code"):
            HANDOFF.correction_task(self.bundle,self.root/"bad-draft.md")

    def job_fixture(self,broken=False):
        scripts=self.root/"runtime/scripts";scripts.mkdir(parents=True)
        shutil.copy2(ROOT/"scripts/handoff_job.py",scripts/"handoff_job.py")
        wrapper="""import importlib.util,json,sys,time
from pathlib import Path
sys.path.insert(0,ROOT_SCRIPTS)
spec=importlib.util.spec_from_file_location('core_job_fixture',Path(ROOT_SCRIPTS)/'handoff.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
load_bundle,HandoffError,compact_result,git,save=core.load_bundle,core.HandoffError,core.compact_result,core.git,core.save
class Fake:
 def authenticate(self):pass
 def execute(self,folder,record,prompt):
  time.sleep(.3)
  p=folder/'fixture-calls';p.write_text((p.read_text() if p.exists() else '')+'call\\n')
  return {'exit_code':0,'stdout':json.dumps({'type':'result','subtype':'success','is_error':False,'result':'Fixture complete','permission_denials':[]}), 'stderr':'','timed_out':False}
if __name__=='__main__':
 core.ClaudeClient=Fake
 DRIVER
""".replace("ROOT_SCRIPTS",repr(str(ROOT/"scripts"))).replace("DRIVER","raise SystemExit(3)" if broken else "core.main()")
        (scripts/"handoff.py").write_text(wrapper,encoding="utf-8")
        spec=importlib.util.spec_from_file_location("local_job_fixture",scripts/"handoff_job.py")
        job=importlib.util.module_from_spec(spec);spec.loader.exec_module(job)
        return job

    def test_local_worker_finishes_and_wait_never_restarts_model(self):
        HANDOFF.prepare(self.project,self.task,self.bundle,["src/"],[])
        job=self.job_fixture()
        with patch.object(job.Path,"cwd",return_value=self.project):
            preview=job.start(self.bundle,self.project)
            self.assertEqual(preview["status"],"preview")
            self.assertFalse((self.bundle/"job.json").exists())
            launched=job.start(self.bundle,self.project,authorized=True)
            self.assertEqual(launched["status"],"launched")
            with self.assertRaises(job.HandoffError):
                job.start(self.bundle,self.project,authorized=True)
            finished=job.wait(self.bundle,self.project,15)
            self.assertEqual(finished["status"],"finished")
            self.assertEqual(finished["outcome"],"completed-needs-review")
            job.wait(self.bundle,self.project,0)
        self.assertEqual((self.bundle/"fixture-calls").read_text(),"call\n")
        self.assertFalse((self.bundle/".job.lock").exists())

    def test_worker_failure_cannot_reuse_previous_result(self):
        HANDOFF.prepare(self.project,self.task,self.bundle,["src/"],[])
        (self.bundle/"run-result.json").write_text('{"status":"old-success"}',encoding="utf-8")
        job=self.job_fixture(broken=True)
        with patch.object(job.Path,"cwd",return_value=self.project):
            job.start(self.bundle,self.project,authorized=True,retry=True)
            done=job.wait(self.bundle,self.project,15)
        self.assertEqual(done["status"],"failed")
        self.assertEqual(done["outcome"],"runner-failed-without-new-result")

    def test_wrong_project_cannot_launch_or_passively_wait(self):
        HANDOFF.prepare(self.project,self.task,self.bundle,["src/"],[])
        job=self.job_fixture()
        with self.assertRaises(job.HandoffError):
            job.start(self.bundle,self.root,authorized=True)
        self.assertFalse((self.bundle/"job.json").exists())

    def test_wait_timeout_is_passive_and_does_not_cancel_job(self):
        HANDOFF.prepare(self.project,self.task,self.bundle,["src/"],[])
        job=self.job_fixture()
        original={"status":"running","job_id":"fixture"}
        HANDOFF.save(self.bundle/"job.json",original)
        with patch.object(job.Path,"cwd",return_value=self.project):
            result=job.wait(self.bundle,self.project,0)
        self.assertTrue(result["wait_timed_out"])
        self.assertEqual(json.loads((self.bundle/"job.json").read_text()),original)
        self.assertFalse((self.bundle/"worktree").exists())

    def test_dead_worker_is_interrupted_without_mutating_or_restarting(self):
        HANDOFF.prepare(self.project,self.task,self.bundle,["src/"],[])
        job=self.job_fixture()
        original={"status":"running","job_id":"fixture","worker_pid":12345}
        HANDOFF.save(self.bundle/"job.json",original)
        with patch.object(job,"alive",return_value=False),patch.object(job.Path,"cwd",return_value=self.project):
            result=job.wait(self.bundle,self.project,0)
        self.assertEqual(result["status"],"interrupted")
        self.assertEqual(json.loads((self.bundle/"job.json").read_text()),original)
        self.assertFalse((self.bundle/"worktree").exists())


class PersonalWorkerRoutingTests(unittest.TestCase):
    def test_launch_and_wait_preserve_project_binding_and_dispatch_locally(self):
        import test_personal_handoff as personal
        import subprocess
        from types import SimpleNamespace
        fixture=personal.PersonalHandoffTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        original=subprocess.run
        calls=[]
        def capture(command,**kwargs):
            if command[0]=="git":return original(command,**kwargs)
            calls.append(command);return SimpleNamespace(returncode=0)
        with patch.object(personal.ENTRY.Path,"cwd",return_value=fixture.first),patch.object(personal.ENTRY,"toolkit_root",return_value=ROOT),patch.object(personal.ENTRY.subprocess,"run",side_effect=capture):
            for action in ("launch","wait"):
                with self.assertRaises(SystemExit):
                    personal.ENTRY.main([action,"--bundle","task","--expected-project",str(fixture.first),*(["--start"] if action=="launch" else [])])
        self.assertIn(str(ROOT/"scripts/handoff_job.py"),calls[0])
        self.assertIn("start",calls[0]);self.assertIn("--start",calls[0])
        self.assertIn("wait",calls[1]);self.assertNotIn("--start",calls[1])
