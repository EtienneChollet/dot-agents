---
name: agent-template
description: >
  A short description of what this agent does.

claude:
  skills: []
  tools: []
  disallowedTools: []
  model: null
  permissionMode: null
  mcpServers: []
  hooks: []
  maxTurns: null
  initialPrompt: null
  memory: null
  effort: null
  background: null
  isolation: null
  color: null

pi:
  tools: []
  skill: null
  extensions: []
  model: null
  fallbackModels: []
  thinking: null
  output: null
  defaultReads: []
  defaultProgress: null
  interactive: null
  maxSubagentDepth: null

codex:
  skills: []
  nickname_candidates: []
  model: null
  model_reasoning_effort: null
  sandbox_mode: null
  mcp_servers: []
---

Your agent instructions go here. This is the system prompt body (maps to Codex's `developer_instructions`).

$ARGUMENTS
