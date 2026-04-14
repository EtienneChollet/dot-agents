---
name: example-agent
description: >
  Example agent demonstrating the canonical format. Use as a reference
  when creating new agents.
  <example>user: 'Review this module for issues'
  assistant: 'Dispatching example-agent to review the module.'</example>
  Do NOT use in production — this is a template.

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

Describe what this agent does in 1-2 sentences.

## Workflow

1. **First step**: What to do first and why
2. **Second step**: What to do next
3. **Final step**: Produce the output

## Constraints

- What the agent must NOT do
- Hard limits on scope

## Output Format

```
## Summary
{1-2 sentences}

## Findings
- {finding with file_path:line evidence}

## Recommendations
- {actionable next step}
```
