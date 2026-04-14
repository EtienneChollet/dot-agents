"""Example PreToolUse hook for a project.

Hooks are Python or shell scripts that run before/after tool calls.
This example blocks a hypothetical dangerous pattern.

Hook types:
  - PreToolUse: runs before a tool call, can block it (exit 2)
  - PostToolUse: runs after a tool call
  - Stop: runs when the agent tries to stop, can block (exit 2)
  - SessionStart: runs once at session start

Environment variables available:
  - TOOL_NAME: name of the tool being called
  - TOOL_INPUT: JSON string of the tool's input parameters
"""
import json
import os
import sys

tool_input = json.loads(os.environ.get("TOOL_INPUT", "{}"))

# Example: block deletion of important files
file_path = tool_input.get("file_path", "")
if file_path.endswith("important_config.yml"):
    print("BLOCKED: Cannot modify important_config.yml", file=sys.stderr)
    sys.exit(2)
