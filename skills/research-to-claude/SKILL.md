---
name: research-to-claude
description: >-
  Prepare and explicitly hand the active chat's researched coding task to local Claude Code.
  Use for requests such as "Claude'u başlat", "Claude başlat", "calude başlat", "Claude'a kodlat"
  or "start Claude for this project". Also prepare the task when requested.
  Questions about how the workflow works and merely reaching the end of a chat do not start Claude.
---

Use the current conversation's task and active project. A personal installation makes this workflow discoverable across local projects; it does not transfer conversation history or authorize another project.

## Resolve this chat's project

Read `references/installation.json` when present to obtain the local toolkit and Python locations. Otherwise this skill's helper can find a toolkit checkout in its parent directories. Run the absolute path of `scripts/handoff_entry.py`, resolved relative to this loaded SKILL.md, with the `context` subcommand. Keep the command's working directory in the active project, not in the skill folder.

Compare the reported Git root with the project attached to this chat or explicitly named by the user. If the chat is projectless, the task is unclear, or the paths disagree, ask for the project folder/task before launching. A Git repository above a generic chat folder is not evidence that the user selected it. Do not scan other chats, reuse the last project, choose the example project, or select the newest task bundle as a fallback.

## Prepare from the current discussion

Inspect the selected project's applicable instructions and current source. Summarize this conversation's research into a concrete TASK.md with sources, decisions, scope, acceptance criteria and reviewed commands. Do not invent file contents or pretend the entire previous chat is visible to Claude. Put the necessary context in the task document; exclude secrets.

Use the registered toolkit's `ARASTIRMA_KOD_AKISI.md` and `handoff/templates/` only as needed. Prepare a fresh bundle outside the selected repository, with explicit allowed edit paths and commands. The helper forwards `prepare` to the toolkit and checks that `--project` matches the current working directory's Git root. It does not start a model.

For independent verification, add reviewed test argv arrays using repeated `--test-command-json` options. Use an absolute native executable path as the first array element. These commands run separately on the host after a successful coding attempt, with the worktree as cwd. They are not inferred from task text or Claude's claims, and they are separate from Claude's Bash allowlist. Review the actual project test code before authorizing execution. If no test commands are configured, report verification as missing.

When the user authorizes Claude to consult Codex for research, prepare with `--enable-research`. A personal installation may already record this preference as `research_default_enabled: true`; the helper then adds that option for new tasks. Respect `--disable-research` for a one-way task. Enabling research prepares a capability; only the explicitly started Claude run can use it. It consumes the Codex subscription allowance and does not access ChatGPT web chats or Deep Research sessions.

Choose only necessary, reviewed, small UTF-8 project files with repeated `--research-context-file` options. No files are shared by default. The researcher receives immutable snapshots of selected files, not the whole repository or live coding changes. Do not include secrets. The task-local MCP exposes only `research_question` and approved context IDs, with default limits of two model calls, 120 seconds each, 240 seconds total, and a 24-hour same-task cache. Failed calls consume the budget; retries do not reset it. Reports are dated source-linked evidence, not authority to widen scope. Shell execution and recursive agents are disabled in the research process; preserve the existing sandbox and managed policy. A source URL is not independent proof that its claim is correct.

## Start only when requested

An explicit request such as "Claude'u başlat" authorizes starting the current agreed task; do not ask the same approval again when project and scope are clear. A request to prepare, explain or install this workflow alone does not authorize a coding run.

Use the bundle created for this conversation. State the original project folder and that Claude's working directory will be its separate Git worktree. Run the helper's `run` command with the bundle, `--expected-project` set to the resolved active project root, and `--start`. Keep the process cwd at that project root. The helper checks cwd and expected project; the runner separately checks the bundle's project and base commit. A mismatch stops before Claude authentication or model execution.

Do not use a different project to get past an error. Missing Git history, dirty tracked files, missing task context, sandbox access restrictions, authentication, quota or denied commands are actionable blockers to report. Do not disable permission boundaries. Retry only when the user explicitly requests it after reviewing the previous result; use `--retry` and preserve partial changes.

## Review the result

Return the actual status, worktree location, result file and diff. A quota/permission error is not success. Use `status --bundle ... --expected-project ...` for the current summary; it starts neither Claude nor tests. Test verification requires the saved host command evidence and must match the current worktree fingerprint. A zero exit code establishes only the configured command's result, not complete functional correctness.

If research was enabled, also return its call count, failures and local report locations. A working Codex/MCP probe does not establish a successful Claude-to-Codex model run when Claude was quota-blocked. Do not weaken local permissions to get a live demonstration to pass.

Explicitly requested test reruns use `verify --bundle ... --expected-project ... --execute-tests`. A `draft-correction --bundle ... --expected-project ... --out ...` command creates a local draft only when completed, current independent tests show a failure. Review the evidence and draft in this conversation. Only an explicit user retry request starts `run --start --retry`; it preserves partial work, archives the prior result, and includes matching saved test evidence. Keep the helper cwd in the original active project for all these commands. Do not automatically commit, merge, push, publish or start a correction loop.

This workflow runs on the computer where the toolkit and Claude Code are installed. It does not create local execution access in an ordinary ChatGPT web/mobile or unrelated remote session.
