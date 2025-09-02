# Repository Guidelines

## Project Structure & Module Organization
- Core: `agent_runner.py` (CLI), `project_manager.py` (projects), utilities in `tools/`.
- Agents: prompts in `agents/` (`core/`, `specialists/`); orchestrator docs in `agents/agent_orchestrator.md`.
- Config: `config/agents.yaml` (registry), model settings in `config/model_assignments_2025.yaml`.
- Integrations: `mcp/` (MCP client, config, setup). Docs in `docs/`.
- Runtime data (gitignored): `projects/`, `feedback/`, `metrics/`.

## Build, Test, and Development Commands
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- Run CLI: `python agent_runner.py init`, then `python agent_runner.py list` or `python agent_runner.py workflow`.
- Run a task: `python agent_runner.py run --agent backend_developer --task "scaffold API" --non-interactive`.
- Menu launcher: `./start.sh`. MCP status/setup: `python agent_runner.py mcp-status` and `./mcp/setup_mcp.sh` (optional).
- Feedback/metrics: `python tools/feedback_collector.py feedback --agent qa_testing --issue "..." --suggestion "..." --priority high`.

## Coding Style & Naming Conventions
- Python (PEP 8): 4-space indent, type hints where practical, clear docstrings.
- Names: `snake_case` for modules/functions, `PascalCase` for classes; agent IDs match filenames (e.g., `agents/specialists/backend_developer.md`).
- Config: prefer YAML (`config/agents.yaml`) and JSON; use `yaml.safe_load`/`safe_dump`.

## Testing Guidelines
- No bundled suite; use `pytest` locally.
- Place tests in `tests/` as `test_*.py`; cover CLI flows (list/run/workflow) and config loading.
- Run: `pytest -q`. Aim for meaningful workflow coverage over line counts.

## Commit & Pull Request Guidelines
- Commits: imperative mood, optional scope prefix (`agents:`, `mcp:`, `cli:`, `docs:`), ≤72‑char subject.
- PRs: clear description, linked issues, sample CLI output if relevant, and updated docs (`README.md`, `agents/*.md`, `docs/`).
- When adding/updating agents, update `config/agents.yaml` and reference the correct `prompt_path`.

## Security & Configuration Tips
- Keep secrets out of git; use `mcp/.env` (see `mcp/.env.example`).
- Do not commit generated data (`projects/`, `feedback/`, `metrics/`) or stray YAML outside `config/` (see `.gitignore`).
- Minimize dependencies; prefer libraries already in `requirements.txt`.

## Agent-Specific Instructions
- Adding an agent: create a prompt in `agents/...`, register it in `config/agents.yaml` with `role`, `capabilities`, and `prompt_path`; verify with `python agent_runner.py list`.

