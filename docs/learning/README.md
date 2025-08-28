# Learning & Continuous Improvement

This folder stores feedback, retrospectives, and lessons learned to improve agents and workflows over time.

Contents:
- `agent_feedback.jsonl` — Append-only event log of feedback entries written by the Agent Manager.
- `retros/` — Retrospectives and postmortems.
- `playbooks/` — Improvement playbooks by area (docs, security, a11y, performance).

Feedback entry schema (JSONL):
```
{
  "timestamp": "ISO8601",
  "agent": "agent_id",
  "task": "task name",
  "outcome": "success|error|warning",
  "notes": "free text",
  "tags": ["security", "docs", "handoff"]
}
```

Usage:
- Use the `AgentManager.record_feedback(...)` helper to append feedback.
- Periodically synthesize `agent_feedback.jsonl` into action items and update playbooks.

