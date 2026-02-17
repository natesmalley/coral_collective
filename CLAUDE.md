# CLAUDE.md

## Project Overview

CoralCollective is a curated collection of 10 specialized Claude Code subagents for software development. The agents live in `.claude/agents/` and are automatically discovered by Claude Code's Task tool.

## Subagents

| Agent | Model | Purpose |
|---|---|---|
| `architect` | Opus | System architecture, technical specs, project planning |
| `fullstack` | Sonnet | Cross-cutting implementation, debugging, MVPs |
| `security` | Opus | Vulnerability audits, security hardening, auth systems |
| `ai-engineer` | Opus | LLM integration, vector DBs, RAG pipelines |
| `backend` | Sonnet | APIs, database schemas, server-side logic |
| `frontend` | Sonnet | UI components, accessibility, responsive design |
| `qa` | Sonnet | Test suites, edge cases, quality validation |
| `devops` | Sonnet | CI/CD, Docker, deployment, monitoring |
| `compliance` | Sonnet | Data governance, privacy, regulatory alignment |
| `technical-writer` | Sonnet | Documentation: specs, guides, API docs, ADRs |

## Design Principles

All agents follow these principles:

- **Tech-agnostic** -- detect the project stack from config files (package.json, pyproject.toml, Cargo.toml, etc.) rather than assuming any specific language or framework
- **Read-first** -- explore the codebase before making changes; understand existing patterns and conventions
- **Minimal-yet-sufficient** -- do exactly what's needed without over-engineering or adding unnecessary abstractions
- **Structured output** -- produce clear deliverables (code, docs, configs) rather than open-ended advice

## Adding or Modifying Agents

Each agent is a single Markdown file in `.claude/agents/`. The file structure:

1. **Role declaration** -- who the agent is and what it does
2. **Workflow** -- step-by-step process the agent follows
3. **Principles** -- constraints and quality standards
4. **Output format** -- what the agent delivers

To add a new agent, create `.claude/agents/<name>.md` following the same structure as existing agents. Use `model: opus` for tasks requiring deep reasoning; use `model: sonnet` for implementation-focused work.

## Repository Structure

```
.claude/
  agents/           # 10 subagent definitions (the core of this repo)
  settings.local.json
CLAUDE.md           # This file
README.md           # Project documentation
LICENSE             # MIT
.gitignore
```
