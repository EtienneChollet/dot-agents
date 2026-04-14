# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Purpose

Harness-agnostic registry for agent and skill definitions. Each agent/skill is
authored once in a canonical format, then compiled into harness-specific configs
for Claude Code (`~/.claude`), Pi (`~/.pi`), and Codex (`~/.codex`) via
`scripts/harness_sync.py`.

**This repo is the source of truth, not the deployment target.** Nothing here
is read directly by any harness at runtime. Definitions must be synced to their
harness-specific paths before they take effect.

## Development

```bash
# Deploy all agents, skills, rules, and projects to all harnesses
python3 ~/.agents/scripts/harness_sync.py

# Force-replace existing files/dirs with symlinks (first run on a machine)
python3 ~/.agents/scripts/harness_sync.py --force

# Delete unmanaged files from deploy targets (stale agents, old skills)
python3 ~/.agents/scripts/harness_sync.py --clean

# Both: force symlinks and purge unmanaged files
python3 ~/.agents/scripts/harness_sync.py --force --clean

# Create a new agent (copy template, fill in what you need)
cp ~/.agents/agents/agent-template.md ~/.agents/agents/my-agent.md

# Create a new skill
mkdir -p ~/.agents/skills/my-skill
# then write ~/.agents/skills/my-skill/SKILL.md
```

**Dependency:** `harness_sync.py` requires PyYAML (`import yaml`).

**No tests or linter exist yet.** The sync script is the only executable;
validate by running it and checking output for `ERROR:` lines.

## Architecture

Each directory has its own README with detailed format documentation.
See `README.md` for the full sync mechanics.

### Instructions (`INSTRUCTIONS.md`)

Global user instructions deployed as `~/.claude/CLAUDE.md` for Claude Code
and `~/.pi/agent/AGENTS.md` for Pi.

### Agents (`agents/`)

Single `.md` files with YAML frontmatter containing harness-specific blocks
(`claude`, `pi`, `codex`). Body is the system prompt.

### Skills (`skills/`)

Directories with `SKILL.md` (required) plus optional `scripts/`, `references/`,
`assets/` subdirectories. Universal format across all harnesses.

### Rules (`rules/`)

Plain markdown files. Symlinked for Claude/Pi; compiled into Codex's `config.toml`.

### Projects (`projects/`)

`main.yml` maps project names to per-machine filesystem paths. Each project can
have a subdirectory with project-specific overrides.
