# Skills

Each skill is a directory with a required `SKILL.md` and optional
subdirectories.

## Structure

```
my-skill/
  SKILL.md           required -- frontmatter (name, description) + instructions
  scripts/           optional -- executables (output enters context, not source)
  references/        optional -- docs loaded on demand
  assets/            optional -- templates, static files
```

The directory name must match the `name` field in SKILL.md frontmatter.

## SKILL.md format

```yaml
---
name: my-skill
description: >
  What this skill does. TRIGGER when user says "phrase1", "phrase2".
  Also trigger for "synonym1", "synonym2". Do NOT trigger for X or Y.
argument-hint: "[optional args description]"
allowed-tools: "Read, Bash, Grep"
---

# My Skill

Instructions the agent follows when invoked (imperative form).
```

### Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | Yes | Skill identifier, becomes the slash command name |
| `description` | Yes | When to trigger -- the agent reads this for discovery |
| `argument-hint` | No | CLI argument hint shown in autocomplete |
| `allowed-tools` | No | Restrict which tools the skill can use |

## Description tips

The description is the primary trigger mechanism. Include:

1. One-sentence purpose
2. `TRIGGER when` -- exact phrases users say
3. Synonyms and edge-case phrasings
4. `Do NOT trigger for` -- negative cases (prevents false triggers)

## Deployment

Skills are universal across harnesses -- the SKILL.md format is the same
for Claude Code, Pi, and Codex. `harness_sync.py` symlinks each skill
directory to:

- `~/.claude/skills/<name>/`
- `~/.pi/agent/skills/<name>/`
- `~/.codex/skills/<name>/`
