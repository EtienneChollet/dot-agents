# Agents

Each agent is a single `.md` file with YAML frontmatter + a markdown body
(the system prompt).

## Format

```yaml
---
name: my-agent
description: >
  When to use this agent. Include trigger phrases and negative triggers.

claude:
  # only fill fields you need, leave rest as null/[]
  disallowedTools: [Edit, Write]
  model: sonnet

pi:
  model: claude-sonnet-4-5

codex:
  model: gpt-5
---

System prompt body goes here (markdown).
```

Copy `agent-template.md` as a starting point -- it lists every available field
for all three harnesses, defaulted to `null`/`[]`.

## Per-harness fields

### Claude Code

| Field | Type | Purpose |
|-------|------|---------|
| `tools` | list | Tool allowlist (omit = inherit all) |
| `disallowedTools` | list | Tool denylist |
| `model` | `haiku` / `sonnet` / `opus` | LLM model (default: inherit parent) |
| `permissionMode` | `default` / `acceptEdits` / `auto` / `dontAsk` / `bypassPermissions` / `plan` | Permission behavior |
| `mcpServers` | object | MCP servers available to this agent |
| `hooks` | object | Lifecycle hooks (PreToolUse, PostToolUse, Stop) |
| `maxTurns` | integer | Max agentic turns before stopping |
| `initialPrompt` | string | Auto-submitted first turn (main session agents) |
| `skills` | list | Skills to preload |
| `memory` | `user` / `project` / `local` | Persistent memory scope |
| `effort` | `low` / `medium` / `high` / `max` | Reasoning effort level |
| `background` | boolean | Always run as background task |
| `isolation` | `worktree` | Run in isolated git worktree |
| `color` | `red` / `blue` / `green` / `yellow` / `purple` / `orange` / `pink` / `cyan` | UI color tag |

### Pi

| Field | Type | Purpose |
|-------|------|---------|
| `tools` | list | Tool allowlist (lowercase: `read, bash, edit, write, grep, find, ls`) |
| `skill` | string | Injected skill content |
| `extensions` | list | Extension load control |
| `model` | string | Model ID (e.g., `claude-sonnet-4-5`) |
| `fallbackModels` | list | Ordered backup models |
| `thinking` | string | Reasoning effort level |
| `output` | string | Result output filepath |
| `defaultReads` | list | Auto-loaded input files |
| `defaultProgress` | boolean | Maintain progress file |
| `interactive` | boolean | Reserved, not enforced |
| `maxSubagentDepth` | integer | Nested delegation limit |

### Codex

| Field | Type | Purpose |
|-------|------|---------|
| `skills` | list | Injected skill content |
| `nickname_candidates` | list | Display name options |
| `model` | string | Model ID (e.g., `gpt-5`) |
| `model_reasoning_effort` | string | Reasoning effort level |
| `sandbox_mode` | string | Sandbox execution mode |
| `mcp_servers` | list | Available MCP servers |

## Deployment

`harness_sync.py` transforms each agent per harness:

- **Claude Code** -> `~/.claude/agents/<name>.md` (flat YAML frontmatter + body)
- **Pi** -> `~/.pi/agent/agents/<name>.md` (flat YAML frontmatter + body)
- **Codex** -> `~/.codex/agents/<name>.toml` (TOML with `developer_instructions`)

Null/empty values are stripped. Only the relevant harness block's fields
appear in the deployed file.
