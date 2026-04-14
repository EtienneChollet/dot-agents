# Rules

Shared prose instruction files (`.md`) deployed to all harnesses.

## Deployment

Behavior differs per harness:

| Harness | Mechanism |
|---------|-----------|
| Claude Code | Symlinked as `~/.claude/rules/` -> `~/.agents/rules/` |
| Pi | Symlinked as `~/.pi/agent/rules/` -> `~/.agents/rules/` |
| Codex | Compiled into `instructions` key in `~/.codex/config.toml` |

For project-scoped deployments, the rules directory is symlinked for
Claude/Pi and compiled into `<project>/.codex/config.toml` for Codex.

## Format

Plain markdown. No frontmatter required. Keep the directory flat (no
subdirectories) since the entire directory is symlinked.
