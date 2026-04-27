# CoralCollective — Skills Edition

A curated collection of 10 specialized Claude **Skills** for software development. Each skill is a focused expert that activates automatically in [Claude.ai](https://claude.ai) when relevant — giving you on-demand access to an architect, security auditor, full-stack debugger, AI engineer, and more.

This is an upgrade from the original Claude Code subagents format. Skills work in Claude.ai (web/mobile) and load contextually based on what you're asking — no explicit invocation required.

---

## Skills

| Skill | Purpose |
|---|---|
| `architect` | System design, technical specs, ADRs, project planning |
| `fullstack` | Cross-cutting implementation, debugging, MVPs |
| `security` | Vulnerability audits, auth systems, security hardening |
| `ai-engineer` | LLM integration, RAG pipelines, vector DBs, prompt engineering |
| `backend` | APIs, database schemas, server-side business logic |
| `frontend` | UI components, accessibility, responsive design |
| `qa` | Test suites, edge case analysis, quality validation |
| `devops` | CI/CD, Docker, IaC, deployment, monitoring |
| `compliance` | GDPR/HIPAA/SOC2, data governance, privacy |
| `technical-writer` | READMEs, API docs, runbooks, ADRs, onboarding guides |

---

## Installation

Each skill lives in its own directory with a `SKILL.md` file. To install, copy the skill directories into your Claude skills folder:

```bash
# Copy all skills
cp -r coral_collective_skills/* ~/.claude/skills/

# Or copy individual skills
cp -r coral_collective_skills/architect ~/.claude/skills/
cp -r coral_collective_skills/security ~/.claude/skills/
```

Once installed, Claude.ai will automatically load the relevant skill based on your request. You can also invoke a skill explicitly by mentioning what you need:

> "Review my authentication flow for security issues"  
> → activates the `security` skill

> "Design a caching layer for my API"  
> → activates the `architect` skill

> "Write tests for the payment module"  
> → activates the `qa` skill

---

## What's Different from Subagents

| | Subagents (Claude Code) | Skills (Claude.ai) |
|---|---|---|
| **Where it works** | Claude Code CLI only | Claude.ai web, mobile, desktop |
| **How it activates** | Task tool delegation | Automatic + explicit |
| **Format** | Agent persona files | Structured SKILL.md with frontmatter |
| **Triggering** | Explicit `Use the X agent` | Contextual + keyword matching |
| **Composable** | Parallel via Task tool | Sequential, contextually loaded |

---

## Skill Design Principles

All skills follow the same design philosophy:

- **Tech-agnostic** — detect the project stack from config files (`package.json`, `pyproject.toml`, `Cargo.toml`, etc.) rather than assuming any specific language or framework
- **Read-first** — explore the codebase before making changes; understand existing patterns and conventions
- **Minimal-yet-sufficient** — do exactly what's needed without over-engineering or adding unnecessary abstractions
- **Structured output** — produce clear deliverables (code, docs, configs) rather than open-ended advice
- **Complete, not partial** — every skill handles happy paths, error cases, and edge cases; no TODOs in output

---

## Skill Structure

Each skill follows the Claude Skills format:

```
skill-name/
└── SKILL.md
    ├── YAML frontmatter (name, description)
    └── Markdown body
        ├── Role declaration
        ├── Workflow (step-by-step process)
        ├── Principles (constraints and standards)
        └── Output format (what the skill delivers)
```

The `description` field in frontmatter is the primary trigger — it tells Claude when to load the skill. Descriptions are intentionally specific and keyword-rich to ensure correct activation.

---

## Adding Your Own Skills

To add a skill, create a new directory with a `SKILL.md`:

```markdown
---
name: your-skill-name
description: What this skill does and when Claude should use it. Be specific about trigger conditions.
---

# Your Skill Title

Brief role declaration.

## Workflow
Step-by-step process...

## Principles
Constraints and standards...

## Output Format
What this skill delivers...
```

See any existing skill in this collection for a reference implementation.

---

## License

MIT — see [LICENSE](LICENSE).

---

## About

CoralCollective is the collective intelligence for evolutionary development — AI agents (and now skills) working as a unified colony to cover every phase of the software development lifecycle.

Original subagents format by [@natesmalley](https://github.com/natesmalley). Skills edition contributed to extend the collection to Claude.ai.
