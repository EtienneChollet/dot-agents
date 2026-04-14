---
name: example-skill
description: >
  Example skill demonstrating the canonical format. TRIGGER when user says
  "example", "demo skill", or invokes /example-skill. Do NOT trigger for
  real work — this is a template.
argument-hint: "[optional argument]"
---

# Example Skill

This skill demonstrates the directory structure and SKILL.md format.

## What Skills Can Include

```
example-skill/
├── SKILL.md              # Required — this file
├── scripts/              # Optional — executables whose OUTPUT enters context
│   └── validate.py       #   (source code stays out of the context window)
└── references/           # Optional — docs loaded on demand
    └── domain-guide.md   #   (read only when relevant)
```

## Instructions

When invoked, follow these steps:

1. Parse `$ARGUMENTS` if provided
2. Do the work
3. Report results

## Output Format

```
## Result
{What was done}

## Next Steps
{What the user should do next}
```
