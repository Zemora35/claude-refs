"""Real local Git/MCP boundaries with fake Codex transport; no service calls."""

import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import test_handoff as fixtures

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import research_bridge as bridge  # noqa: E402
import research_mcp as mcp  # noqa: E402

HANDOFF = fixtures.HANDOFF
QUESTION = "What is the official Python unittest recommendation for checking numeric equality?"


class FakeCodex:
    def __init__(self, failure=False, unsafe=False, report=None):
        self.auth_calls = self.calls = 0
        self.failure, self.unsafe = failure, unsafe
        self.report = report or {"summary": "Use unittest assertions.", "recommendation": "Use assertEqual for exact integers.",
                                 "sources": [{"title": "Python unittest", "url": "https://docs.python.org/3/library/unittest.html"}], "uncertainties": []}

    def authenticate(self):
        self.auth_calls += 1

    def execute(self, workspace, schema, prompt, timeout):
        self.calls += 1
        self.prompt = prompt
        events = [{"type": "item.completed", "item": {"type": "web_search", "action": {"type": "search", "query": "Python unittest docs"}}},
                  {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(self.report)}},
                  {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 50}}]
        if self.unsafe:
            events.insert(0, {"type": "item.completed", "item": {"type": "command_execution", "command": "unexpected"}})
        return {"stdout": "\n".join(json.dumps(e) for e in events), "stderr": "", "exit_code": 1 if self.failure else 0, "timed_out": self.failure}


class ResearchTests(unittest.TestCase):
    git = fixtures.HandoffTests.git

    def setUp(self):
        fixtures.HandoffTests.setUp(self)

    def run_research(self, callback, **limits):
        HANDOFF.prepare(self.project, self.task, self.bundle, ["src/"], [],
                        research_config={"files": ["src/app.py"], **limits})
        return self.run_existing(callback)

    def run_existing(self, callback, retry=False):
        class AskingClaude(fixtures.FakeClaude):
            def execute(inner, folder, contract, prompt):
                config = json.loads((folder / "research-mcp.json").read_text(encoding="utf-8"))
                token = config["mcpServers"]["research"]["env"]["CLAUDE_REFS_RESEARCH_SESSION"]
                callback(folder, contract, token)
                return super().execute(folder, contract, prompt)

        return HANDOFF.execute_bundle(self.bundle, start=True, retry=retry, expected_project=self.project, client=AskingClaude())

    def test_research_is_opt_in_and_preview_creates_no_live_capability(self):
        HANDOFF.prepare(self.project, self.task, self.bundle, ["src/"], [], research_config={"files": ["src/app.py"]})
        record = HANDOFF.execute_bundle(self.bundle)
        self.assertTrue(record["research"]["enabled"])
        self.assertFalse((self.bundle / "research/active.json").exists())
        self.assertFalse((self.bundle / "worktree").exists())
        self.assertIn("mcp__research__research_question", HANDOFF.cli_arguments("claude", self.bundle, record))

    def test_real_report_evidence_and_same_question_cache(self):
        backend = FakeCodex()

        def ask(folder, record, token):
            first = bridge.research(folder, record, token, QUESTION, ["src/app.py"], client=backend, now=100)
            second = bridge.research(folder, record, token, QUESTION, ["src/app.py"], client=backend, now=101)
            self.assertFalse(first["cached"])
            self.assertTrue(second["cached"])
            self.assertIn("VALUE = 1", backend.prompt)
            self.assertEqual(first["web_search_calls"], 1)
            self.assertFalse(first["source_claims_independently_verified"])

        result = self.run_research(ask)
        self.assertEqual(backend.calls, 1)
        self.assertEqual(result["research"]["calls_used"], 1)
        self.assertTrue((self.bundle / "research/call-1/report.json").is_file())
        self.assertFalse((self.bundle / "research/active.json").exists())
        self.assertFalse((self.bundle / "research-mcp.json").exists())

    def test_budget_persists_across_server_restart_and_explicit_retry(self):
        backend = FakeCodex()

        def ask(folder, record, token):
            bridge.research(folder, record, token, QUESTION, client=backend)
            bridge.research(folder, record, token, QUESTION + " Also compare assertTrue.", client=backend)

        self.run_research(ask)

        def blocked(folder, record, token):
            with self.assertRaisesRegex(bridge.ResearchError, "budget exhausted"):
                bridge.research(folder, record, token, QUESTION + " A third question.", client=backend)

        result = self.run_existing(blocked, retry=True)
        self.assertEqual(backend.calls, 2)
        self.assertEqual(result["research"]["calls_used"], 2)

    def test_failed_call_consumes_budget_and_never_becomes_cached_success(self):
        backend = FakeCodex(failure=True)

        def ask(folder, record, token):
            with self.assertRaises(bridge.ResearchError):
                bridge.research(folder, record, token, QUESTION, client=backend)
            self.assertFalse((folder / "research/cache").exists())
            with self.assertRaisesRegex(bridge.ResearchError, "no automatic retry"):
                bridge.research(folder, record, token, QUESTION, client=backend)

        result = self.run_research(ask, max_calls=1)
        self.assertEqual(backend.calls, 1)
        self.assertEqual(result["research"]["failed_calls"], 1)

    def test_unapproved_context_and_incorrect_session_are_rejected_before_auth(self):
        backend = FakeCodex()

        def ask(folder, record, token):
            for contexts in (["../other-project/file.py"], ["README.md"], [".env"]):
                with self.assertRaisesRegex(bridge.ResearchError, "context IDs"):
                    bridge.research(folder, record, token, QUESTION, contexts, client=backend)
            with self.assertRaisesRegex(bridge.ResearchError, "another run"):
                bridge.research(folder, record, "wrong-session", QUESTION, client=backend)

        self.run_research(ask)
        self.assertEqual(backend.auth_calls, 0)

    def test_context_snapshot_tamper_is_rejected_before_start(self):
        HANDOFF.prepare(self.project, self.task, self.bundle, ["src/"], [], research_config={"files": ["src/app.py"]})
        next((self.bundle / "research/context").glob("*.txt")).write_text("Changed context", encoding="utf-8")
        with self.assertRaisesRegex(bridge.ResearchError, "context changed"):
            HANDOFF.load_bundle(self.bundle)

    def test_context_boundaries_sensitive_names_and_size_are_rejected(self):
        (self.project / ".env").write_text("fixture", encoding="utf-8")
        (self.project / "secret.txt").write_text("fixture", encoding="utf-8")
        (self.project / "large.txt").write_text("x" * 32001, encoding="utf-8")
        for name in ("../TASK.md", str(self.task), ".env", "secret.txt", "large.txt", "src/app.py:stream"):
            with self.assertRaises(bridge.ResearchError):
                bridge.policy(self.project, [name])

    def test_cache_expires_and_consumes_a_new_bounded_call(self):
        backend = FakeCodex()

        def ask(folder, record, token):
            bridge.research(folder, record, token, QUESTION, client=backend, now=100)
            result = bridge.research(folder, record, token, QUESTION, client=backend, now=3701)
            self.assertFalse(result["cached"])

        self.run_research(ask, cache_hours=1)
        self.assertEqual(backend.calls, 2)

    def test_unexpected_command_event_is_not_success(self):
        def ask(folder, record, token):
            with self.assertRaisesRegex(bridge.ResearchError, "disallowed action"):
                bridge.research(folder, record, token, QUESTION, client=FakeCodex(unsafe=True))

        self.run_research(ask)

    def test_report_requires_public_sources_and_bounded_fields(self):
        report = FakeCodex().report
        for url in ("http://example.com", "https://localhost/a", "https://127.0.0.1/a", "https://user:password@example.com/a"):
            invalid = {**report, "sources": [{"title": "bad", "url": url}]}
            with self.assertRaises(bridge.ResearchError):
                bridge.validate_report(invalid)
        with self.assertRaises(bridge.ResearchError):
            bridge.validate_report({**report, "sources": []})

    def test_parallel_request_lock_does_not_start_another_model(self):
        backend = FakeCodex()

        def ask(folder, record, token):
            lock = folder / "research/.request.lock"
            lock.write_text("held", encoding="utf-8")
            try:
                with self.assertRaisesRegex(bridge.ResearchError, "Another research"):
                    bridge.research(folder, record, token, QUESTION, client=backend)
            finally:
                lock.unlink()

        self.run_research(ask)
        self.assertEqual(backend.calls, 0)

    def test_native_codex_arguments_disable_execution_without_bypassing_policy(self):
        arguments = bridge.codex_arguments("codex", self.root, self.task)
        self.assertIn("features.shell_tool=false", arguments)
        self.assertIn("features.multi_agent=false", arguments)
        self.assertIn("read-only", arguments)
        self.assertNotIn("--ignore-rules", arguments)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", arguments)

    def test_api_environment_is_not_silently_billed(self):
        with patch.dict(os.environ, {"CODEX_API_KEY": "fixture-not-a-real-key"}):
            with self.assertRaisesRegex(bridge.ResearchError, "billing authorization"):
                bridge.CodexClient().authenticate()

    def test_mcp_protocol_negotiation_strict_arguments_and_notification_handling(self):
        calls = []

        def ask(folder, record, token):
            server = mcp.ResearchServer(folder, record, token, researcher=lambda *args: calls.append(args) or {"report": "fixture"})
            source = io.StringIO("\n".join(json.dumps(value) for value in [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "research_question", "arguments": {"question": QUESTION, "file": "unapproved"}}},
                {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "research_question", "arguments": {"question": QUESTION}}},
            ]) + "\n")
            destination = io.StringIO()
            mcp.serve(server, source, destination)
            replies = [json.loads(line) for line in destination.getvalue().splitlines()]
            self.assertEqual(len(replies), 4)
            self.assertEqual(replies[1]["result"]["tools"][0]["name"], "research_question")
            self.assertTrue(replies[2]["result"]["isError"])
            self.assertFalse(replies[3]["result"]["isError"])

        self.run_research(ask)
        self.assertEqual(len(calls), 1)

    def test_real_stdio_process_discovers_tool_without_model_call(self):
        def ask(folder, record, token):
            requests = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
                        {"jsonrpc": "2.0", "method": "notifications/initialized"},
                        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]
            environment = {**os.environ, "CLAUDE_REFS_RESEARCH_SESSION": token}
            response = subprocess.run([sys.executable, "-B", str(Path(mcp.__file__)), "--bundle", str(folder), "--expected-project", str(self.project)],
                                      cwd=record["worktree"], env=environment, input="\n".join(json.dumps(v) for v in requests) + "\n",
                                      text=True, capture_output=True, encoding="utf-8", check=True, timeout=15)
            replies = [json.loads(line) for line in response.stdout.splitlines()]
            self.assertEqual(replies[-1]["result"]["tools"][0]["name"], "research_question")

        self.run_research(ask)

    def test_empty_and_out_of_range_limits_are_rejected(self):
        for kwargs in ({"max_calls": 0}, {"max_calls": True}, {"timeout": 301}, {"total_seconds": 0}, {"cache_hours": 169}):
            with self.assertRaises(bridge.ResearchError):
                bridge.policy(self.project, [], **kwargs)

    def test_known_credential_pattern_is_rejected_before_model_authentication(self):
        (self.project / "context.txt").write_text("sk-" + "x" * 30, encoding="utf-8")
        with self.assertRaisesRegex(bridge.ResearchError, "credential"):
            bridge.policy(self.project, ["context.txt"])
        backend = FakeCodex()

        def ask(folder, record, token):
            with self.assertRaises(bridge.ResearchError):
                bridge.research(folder, record, token, "Check this value: " + "sk-" + "x" * 30, client=backend)

        self.run_research(ask)
        self.assertEqual(backend.auth_calls, 0)

    def test_exhausted_time_ledger_is_not_reset_by_a_new_request(self):
        backend = FakeCodex()

        def ask(folder, record, token):
            bridge.write_json(folder / "research/state.json", {"attempts": [{"number": 1, "status": "reserved", "seconds": 240}]})
            with self.assertRaisesRegex(bridge.ResearchError, "budget exhausted"):
                bridge.research(folder, record, token, QUESTION, client=backend)

        self.run_research(ask)
        self.assertEqual(backend.calls, 0)

    def test_capability_is_revoked_when_the_coding_transport_fails(self):
        class FailingClaude(fixtures.FakeClaude):
            def execute(self, folder, contract, prompt):
                raise OSError("Transport fixture failure")

        HANDOFF.prepare(self.project, self.task, self.bundle, ["src/"], [], research_config={"files": []})
        with self.assertRaises(OSError):
            HANDOFF.execute_bundle(self.bundle, start=True, expected_project=self.project, client=FailingClaude())
        self.assertFalse((self.bundle / "research/active.json").exists())
        self.assertFalse((self.bundle / "research-mcp.json").exists())
        self.assertFalse((self.bundle / ".running.lock").exists())

    def test_report_without_web_search_evidence_is_rejected(self):
        response = FakeCodex().execute(self.root, self.task, "fixture", 10)
        response["stdout"] = "\n".join(line for line in response["stdout"].splitlines() if json.loads(line).get("item", {}).get("type") != "web_search")
        with self.assertRaisesRegex(bridge.ResearchError, "web-search evidence"):
            bridge.parse_events(response)

    def test_provider_quota_error_is_classified(self):
        events = [{"type": "error", "message": "You've hit your usage limit"},
                  {"type": "turn.failed", "error": {"message": "Usage limit reached"}}]
        response = {"stdout": "\n".join(json.dumps(event) for event in events), "stderr": "", "exit_code": 1, "timed_out": False}
        with self.assertRaises(bridge.ResearchError) as error:
            bridge.parse_events(response)
        self.assertEqual(error.exception.code, "blocked-service-limit")

    def test_provider_quota_blocks_different_questions_in_the_same_run(self):
        backend = FakeCodex()

        def quota(*args):
            backend.calls += 1
            raise bridge.ResearchError("Provider quota fixture", "blocked-service-limit")

        backend.execute = quota

        def ask(folder, record, token):
            with self.assertRaises(bridge.ResearchError):
                bridge.research(folder, record, token, QUESTION, client=backend)
            with self.assertRaisesRegex(bridge.ResearchError, "no automatic retry"):
                bridge.research(folder, record, token, QUESTION + " Another question.", client=backend)

        self.run_research(ask)
        self.assertEqual(backend.calls, 1)

    def test_explicit_coding_retry_allows_reviewed_research_retry_without_resetting_budget(self):
        failing = FakeCodex(failure=True)

        def fail(folder, record, token):
            with self.assertRaises(bridge.ResearchError):
                bridge.research(folder, record, token, QUESTION, client=failing)

        self.run_research(fail)
        backend = FakeCodex()

        def succeed(folder, record, token):
            result = bridge.research(folder, record, token, QUESTION, client=backend)
            self.assertFalse(result["cached"])

        result = self.run_existing(succeed, retry=True)
        self.assertEqual(backend.calls, 1)
        self.assertEqual(result["research"]["calls_used"], 2)


if __name__ == "__main__":
    unittest.main()
