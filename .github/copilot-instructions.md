## Quick repo snapshot

This repository currently contains minimal metadata for documentation: `.cursorrules` (project doc-writing rules). No obvious language-specific files (e.g. `package.json`, `pyproject.toml`, `README.md`, `src/`) were present when this guide was generated—probe the workspace first (see "First steps").

## What this guide is for

Short, actionable rules for AI coding agents to get productive in this codebase: how to discover the project's structure, where to apply changes, and how to preserve project conventions already encoded in `.cursorrules`.

## First steps (always run these on a fresh checkout)

1. List top-level files and directories. If the repo is empty, ask the user where the source lives.
2. Search for common build/test manifests and CI: `package.json`, `pyproject.toml`, `requirements.txt`, `setup.py`, `go.mod`, `Cargo.toml`, `README.md`, `.github/workflows/`.
3. If you find a manifest, run the matching quick health commands (replace examples with detected tools):

```bash
npm install && npm test

python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && pytest -q

go test ./...
```

Do not run commands until you confirm the corresponding files exist.

## Project-specific conventions discovered

- `.cursorrules` exists and encodes the documentation style and publishing rules. Follow its guidance when editing docs: simple language, code-first examples, shorter pages, and update `docs/docs.json` when adding pages.
- Docs components referenced in `.cursorrules`: `Accordion`, `Tabs`, `CodeGroup`, `ParamField`, and `ResponseField`. When adding docs, prefer the code-first layout recommended there.

## How to make code changes (AI agent workflow)

1. Run the repo scan above. If no language files are present, ask the user to point to the application code or monorepo root.
2. When editing docs, preserve `.cursorrules` rules: keep changes minimal and focused; ask clarifying questions only if required information is missing.
3. For feature or bug fixes: find the language-specific manifest, run tests locally, implement minimal change, run tests again, open a branch and create a PR draft (include test and short description).

## Where to look for important examples and patterns

- `./docs/` and `./docs/docs.json` — if present, they control doc structure referenced in `.cursorrules`.
- `.cursorrules` — the authoritative doc-writing rules; follow them verbatim for style and placement of examples.
- `.github/workflows/` — CI build/test commands; prefer matching local commands to CI steps.

## PR and commit guidance for AI agents

- Keep commits small and focused. Reference the issue or user request when provided.
- Update docs and tests alongside code changes. If you change doc structure, update `docs/docs.json` accordingly.

## When something is missing or ambiguous (how to ask the user)

Be explicit and minimal. Examples of good questions:

- "I don't see a `package.json`, `pyproject.toml`, or `README.md`. Where is the source code or which language/runtime should I target?"
- "Which CI workflow is authoritative for build/test steps: the repository's `.github/workflows/*` or a separate CI system?"

## Safety and style notes for agents

- Do not invent project files or commands. If you must propose a change that adds files (README, manifest), mark it as an assumption and ask for confirmation.
- When editing docs, follow `.cursorrules`: code-first snippets near the top, use Mintlify components if the docs site uses them, and keep prose simple.

---

If this file missed anything you expected (build commands, important directories, or example files), please point me to the repository root or paste `ls -la`/`tree` output and I'll update this immediately.
