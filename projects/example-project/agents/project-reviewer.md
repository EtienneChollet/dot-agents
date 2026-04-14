---
name: project-reviewer
description: >
  Example project-scoped agent. Project agents are deployed only to the
  project directory, not globally.

claude:
  tools: []
  disallowedTools: [Edit, Write]
  model: null
  permissionMode: null
  mcpServers: []
  hooks: []
  maxTurns: null
  initialPrompt: null
  skills: []
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

## Task

Project-scoped agent that only exists within this project's context.

## Workflow

1. Read the relevant files
2. Analyze against project conventions
3. Report findings

## Output Format

```
## Findings
- {finding}
```
