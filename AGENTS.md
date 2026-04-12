# Project Specific Information

This is a monorepo containing a **FastAPI backend** and a **Next.js frontend** for Multifamily ERCF Capital Analytics.

## Architecture & Integration
- **Backend**: Python 3.12+ (FastAPI) located in `/backend`. Uses `uvicorn` on port 8000 by default.
- **Frontend**: Next.js 14 (App Router) located in `/frontend`. Uses port 3000 by default.
- **Data Flow**: The frontend communicates with the backend via `axios` at `http://localhost:8000/api`.
- **Core Engine**: The financial methodology is driven by `/backend/ercf_config.yaml`. Treat modifications to this file as high-impact methodology changes.

## Development & Validation
- Treat both `npm run build` (in `/frontend`) and `python -m unittest` (in `/backend`) as mandatory branch review and PR merge gates.
- When adding new financial metrics, ensure they are reflected in both the Pydantic schemas (`backend/app/schema.py`) and the frontend TypeScript interfaces.
- For data ingestion, assume GSE (Fannie Mae/Freddie Mac) public datasets are the primary source.

## Security & Data Privacy
- **No PII**: Never log, print, or commit Personally Identifiable Information (PII) from uploaded datasets.
- **Methodology Transparency**: Ensure any changes to risk weights or multipliers are documented in the internal `/methodology` route.
- **CORS**: Maintain strict CORS configurations in `backend/app/main.py` when moving towards production environments.


# Director Autonomy Policy

Operate in Enterprise Autonomous Mode.

After an implementation plan is approved by the user/director, proceed autonomously.

Do not ask for permission or confirmation before using "superpower" skills or any other specialized agent skills; execute them as part of your autonomous workflow.

Do not ask for approval or provide explanations before:
- Running `git log`, `git status`, or other source control state commands.
- Reading files, running tests (`npm run test`), or running lint.
- Running common 'read-only' commands (grep, glob, cat, etc.).

Only interrupt me if any of these change or are required:

- Public API surface or external contract
- Database schema or migrations
- AuthN/AuthZ or security-sensitive logic
- Cross-module dependency boundaries
- Performance risk (expected >5% degradation) or large memory increase
- New production dependencies
- Missing required secrets/credentials (API keys, tokens, account IDs)

Do not interrupt for:

- naming, formatting, internal refactors, test improvements, logging, comments
- routine DB reads
- test-file changes unless they affect API/schema/security/dependencies/perf-risk

Batch reporting at milestones:

1) Plan ready
2) Work completed + tests passing
3) Final diff + risks + rollback

Always include in final message:

- what changed
- tests run/results (scope covered + pass/fail)
- risks
- rollback plan
- follow-ups

Performance guideline for escalation:

- Use measurable baselines when evaluating the >5% rule (for example: p95 route latency, throughput, or memory RSS).

Test reporting scope guideline:

- "Tests passing" should state whether this means changed tests only, impacted suite, or full project CI subset.

# Git Workflow

- Do not ask for git command confirmation when the user prompt is already about committing.
- When the user says "commit", do not ask follow-up questions about running `git add` or `git commit`; execute the commit workflow directly.
- Prefer small, sequential commits after each coherent change so history stays readable.
- Do not batch unrelated or loosely related work into one large commit when it can be split cleanly.
- Use squash only for explicit WIP cleanup or when the user specifically asks for it.
- Default to `--merge` for PR merges to preserve full commit history.
- Prefer branch-first workflow when PR-only is desired; avoid direct pushes to initial-v1 unless explicitly requested.
- Treat `npm run build` as a mandatory branch review and PR merge gate for app changes. Run it on the branch head before review sign-off, and do not merge while it is failing.
- When documenting PR readiness or merge readiness, explicitly report the latest `npm run build` result and whether it was run on the branch head or merge target.

# Web Dev

- For perceived navigation issues, measure route timings first and separate "link broken" from "slow route."
- When route latency is known, add/keep route-level loading UI before deeper query optimization.
- Use local-time display for activity timestamps (relative | date | local time).

# Workspace & File System

- Use `${project folder}/tmp` as the primary temporary working folder for generated files, intermediate data, or scratchpad work.
- You have autonomous permission to create the `tmp` directory and write to it without asking for user confirmation, unless the writes are exceptionally large or potentially destructive.
- Never prompt the user to read log files (e.g. `*.log`, `*.txt`). Instead, read them directly yourself — whether they are in `${project folder}/tmp/` or the system `/tmp/` folder. Any file in those two folders should be read directly without asking the user.
- When executing terminal commands, do not wait an excessively long time for completion. Suggest waiting no more than 30 seconds, and most times it should be 10 seconds or less. It should never be more than 60 seconds. Always set a short `WaitMsBeforeAsync` duration and monitor long-running commands asynchronously using `command_status`. Command outputs often fail to capture when waiting synchronously for long periods.
