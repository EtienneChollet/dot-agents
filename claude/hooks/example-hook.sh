#!/bin/bash
# Example SessionStart hook: inject context at the start of every session.
#
# Hook scripts receive context via stdin (JSON) and environment variables.
# Their stdout is injected into the conversation as system context.
#
# To use: add this to claude/settings.json under hooks.SessionStart:
#   {
#     "matcher": "startup",
#     "hooks": [{ "type": "command", "command": "~/.claude/hooks/example-hook.sh" }]
#   }

echo "Session started on $(hostname) at $(date +%Y-%m-%d)"
echo "Working directory: $(pwd)"
