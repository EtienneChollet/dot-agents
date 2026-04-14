# Example Rule

Rules are plain markdown files that get loaded into every agent's context.
Use them for conventions, standards, and guidelines that apply across
all projects.

## When to Use Rules

- Coding standards and style guides
- Git conventions (commit format, branch naming)
- Communication preferences
- Development workflow (TDD, review process)
- Tool preferences (package managers, linters)

## Format

No frontmatter required. Just plain markdown. Keep the `rules/` directory
flat (no subdirectories) since the entire directory is symlinked.

Rules are loaded globally — every agent in every project sees them.
For project-specific rules, put them in `projects/<name>/rules/` instead.
