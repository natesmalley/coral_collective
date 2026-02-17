# CoralCollective

A curated collection of 10 specialized Claude Code subagents for software development. Each agent is a focused expert that Claude Code can delegate to via the Task tool, giving you on-demand access to an architect, security auditor, full-stack debugger, and more.

## Agents

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

Opus agents handle tasks requiring deeper reasoning (architecture, security, AI/ML). Sonnet agents handle implementation-focused work where speed matters.

## Installation

Copy the `.claude/agents/` directory into your project:

```bash
# From your project root
cp -r path/to/coral-collective/.claude/agents/ .claude/agents/
```

Or clone and copy:

```bash
git clone https://github.com/coral-collective/coral-collective.git
cp -r coral-collective/.claude/agents/ your-project/.claude/agents/
```

The agents will be available the next time you start Claude Code in that project.

## Usage

Claude Code automatically discovers agents in `.claude/agents/`. You can invoke them in two ways:

**Let Claude decide** -- just describe a task and Claude Code will delegate to the right subagent when appropriate.

**Explicitly request** -- ask Claude Code to use a specific agent:

```
Use the security agent to audit the authentication flow in src/auth/
```

```
Use the architect agent to design a caching layer for the API
```

```
Use the qa agent to write tests for the payment module
```

## Design Principles

All agents follow these principles:

- **Tech-agnostic** -- agents detect the project stack from config files rather than assuming any specific language or framework
- **Read-first** -- agents explore the codebase before making changes, understanding existing patterns and conventions
- **Minimal-yet-sufficient** -- agents do exactly what's needed without over-engineering or adding unnecessary abstractions
- **Structured output** -- agents produce clear deliverables (code, docs, configs) rather than open-ended advice

## License

MIT -- see [LICENSE](LICENSE).
