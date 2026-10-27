---
name: research-to-claude
description: >-
  Prepare and explicitly hand the active chat's researched coding task to local Claude Code.
  Use for requests such as "Claude'u başlat", "Claude başlat", "calude başlat", "Claude'a kodlat"
  or "start Claude for this project". Also prepare the task when requested.
  Questions about how the workflow works and merely reaching the end of a chat do not start Claude.
---

Use this conversation's agreed task and active project. Personal installation enables discovery across chats; it transfers neither chat history nor authorization for another project.

## Bind the project

Read `references/installation.json` for toolkit/Python locations. Run this skill's absolute `scripts/handoff_entry.py context` from the active project. Match its Git root to the user-selected project. Missing/mismatching context needs clarification; never fall back to another chat, the last project, the newest bundle or an example. Keep helper cwd at the selected Git root and pass matching `--project` / `--expected-project`. Preserve dirty files without stash/reset or automatic commits; use the project's authorized source-preservation workflow when needed.

## Prepare one small task

Prepare a fresh bundle outside the repository. Declare **one or two actual issue groups** using repeated `--issue-group`; keep remaining issues in a separate backlog. Do not relabel ten bugs as one group. New TASK.md files must be 80–12000 UTF-8 bytes: relevant paths, observed failure, decisions and acceptance criteria. Link raw evidence instead of pasting logs or duplicating command lists. Read focused source/error excerpts first. Never edit existing sealed bundles in place.

Review actual test code; use absolute native argv arrays:

- `--target-test-commands-file` / `--target-test-command-json`: narrow tests for these issues, automatically permitted to Claude while coding.
- `--test-commands-file` / `--test-command-json`: final host suite, once after independent targeted tests pass. Do not grant it through Claude's `--allow-command`. Failed targets skip the final suite; a skipped suite is never a verified full pass.
- `--allow-command`: only other necessary, reviewed setup/inspection commands. No general shells, chains, publishing, unapproved installs or unrelated commands. Missing meaningful tests must be reported, not invented.

Use toolkit `ARASTIRMA_KOD_AKISI.md` and templates only as needed. Preparing starts neither Claude nor tests.

## Launch; let the local worker wait

An explicit "Claude'u başlat" authorizes this agreed task. Do not ask again when project/scope are clear. State the original project and its separate coding worktree.

Prefer `handoff_entry.py launch --bundle <this-bundle> --expected-project <active-root> --start`. A hidden local Python worker runs the existing bounded runner and verification. Launch acknowledgement proves worker launch, not successful Claude authentication or coding. It saves `job.json`, logs, progress, `RESULT.md`, `run-result.json` and `changes.patch` without model polling. Never duplicate an active job.

Use the host's approved execution/network permissions. A sandbox may terminate child processes when its command exits; do not bypass that boundary. Passive wait reports an exited worker as `interrupted` and preserves stale locks for inspection, never automatic restart. An active worker also makes earlier attempt evidence non-current.

**Do not poll with model turns every minute.** Use a native completion event if available. Otherwise return the job/result location and let the worker continue locally; do not promise an automatic chat notification. On a later user result request, inspect once with `status` and `wait --timeout-seconds 0`. A local operator can use `wait --timeout-seconds 600` to block in Python; waiting calls no model, tests or retries. Do not turn bounded waits into a model polling loop. Foreground `run --start` remains available when the host waits without repeated inference.

Network, quota, permissions and prerequisites are blockers, not success. Preserve permission boundaries and project/provider/billing identity. Retry only when the user explicitly requests it after reviewing the previous result: `launch --start --retry` or foreground `run --start --retry`. Preserve partial code and archived evidence. Do not automatically commit, merge, push, publish or start a correction loop.

## Review saved evidence

Report actual worker/model status, worktree, changed paths, patch and evidence. `status` starts no model or tests. Console/retry summaries are compact; raw stdout/stderr stays in local verification files. Evidence must match the current worktree fingerprint. A command's zero exit code is not complete functional correctness.

Explicit test reruns use `verify --bundle ... --expected-project ... --execute-tests`, again targeted before final. `draft-correction` only creates a local draft from current completed failing evidence, including verified targeted failures; it starts no model. Review before an explicitly requested retry, preserving scope and meaningful assertions.

## Optional bounded research

Preserve personal `research_default_enabled` and per-task `--enable-research` / `--disable-research`. Enabling prepares a capability; only an explicitly started Claude run uses it. It consumes Codex subscription allowance, not web ChatGPT or Deep Research. No files are shared by default. Select only necessary small UTF-8 files with `--research-context-file`; never put secrets/private source in a question.

The task-local MCP only exposes `research_question` and approved context IDs. Defaults: two calls, 120 seconds each, 240 seconds total, same-task 24-hour cache. Failures consume budget; retries do not reset it. Research has read-only scope, shell/recursive agents disabled and managed policy preserved. No Bash or background-agent bypass. Reports are source-linked evidence, not authority to expand scope. Return actual call/failure counts; probes are not successful model calls. This requires the local installed toolkit and Claude Code; web/mobile chat gains no local execution access.
