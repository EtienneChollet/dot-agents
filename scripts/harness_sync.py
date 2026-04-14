#!/usr/bin/env python3
"""Compile canonical agent/skill/rule definitions to harness-specific configs.

Reads from ~/.agents/ (this repo) and deploys to:
  - Claude Code: ~/.claude/agents/, ~/.claude/skills/, ~/.claude/rules/
  - Pi:          ~/.pi/agent/agents/, ~/.pi/agent/skills/, ~/.pi/agent/rules/
  - Codex:       ~/.codex/agents/, ~/.codex/skills/, ~/.codex/config.toml

Flags:
  --force  Replace existing files/dirs with symlinks (default: skip with error)
  --clean  Delete unmanaged files from deploy targets (default: report only)
"""
from __future__ import annotations

import os
import re
import shutil
import socket
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

REPO = Path(__file__).resolve().parent.parent  # ~/.agents/
HOME = Path.home().resolve()

CLAUDE_INSTRUCTIONS = HOME / ".claude" / "CLAUDE.md"
CLAUDE_AGENTS = HOME / ".claude" / "agents"
CLAUDE_SKILLS = HOME / ".claude" / "skills"
CLAUDE_RULES = HOME / ".claude" / "rules"

PI_INSTRUCTIONS = HOME / ".pi" / "agent" / "AGENTS.md"
PI_AGENTS = HOME / ".pi" / "agent" / "agents"
PI_SKILLS = HOME / ".pi" / "agent" / "skills"
PI_RULES = HOME / ".pi" / "agent" / "rules"

CODEX_AGENTS = HOME / ".codex" / "agents"
CODEX_SKILLS = HOME / ".codex" / "skills"
CODEX_CONFIG = HOME / ".codex" / "config.toml"

CLAUDE_SETTINGS = HOME / ".claude" / "settings.json"
CLAUDE_SETTINGS_LOCAL = HOME / ".claude" / "settings.local.json"
CLAUDE_HOOKS = HOME / ".claude" / "hooks"
CLAUDE_MCP = HOME / ".claude" / ".mcp.json"

PI_DEPLOY = HOME / ".pi" / "agent"
PI_ROOT = HOME / ".pi"

# Items in ~/.agents/pi/ that deploy to ~/.pi/ instead of ~/.pi/agent/
PI_ROOT_ITEMS = {"extensions-optional"}

SKIP_AGENTS = {"agent-template", "README"}

FORCE = False  # set via --force flag; replaces existing files/dirs with symlinks
CLEAN = False  # set via --clean flag; deletes unmanaged files from deploy targets

# Valid harness-specific frontmatter fields (from README.md)
CLAUDE_FIELDS = {
    "tools", "disallowedTools", "model", "permissionMode",
    "mcpServers", "hooks", "maxTurns", "initialPrompt",
    "skills", "memory", "effort", "background", "isolation", "color",
}
PI_FIELDS = {
    "tools", "skill", "extensions", "model", "fallbackModels",
    "thinking", "output", "defaultReads", "defaultProgress",
    "interactive", "maxSubagentDepth",
}
CODEX_FIELDS = {
    "skills", "nickname_candidates", "model", "model_reasoning_effort",
    "sandbox_mode", "mcp_servers",
}


class _Folded(str):
    """Marker: serialize as YAML folded block scalar (>)."""


def _folded_representer(dumper: yaml.Dumper, data: _Folded) -> yaml.Node:
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=">")


yaml.add_representer(_Folded, _folded_representer)


def parse_agent(path: Path) -> Tuple[Dict[str, Any], str]:
    """Parse canonical agent .md -> (frontmatter dict, body string)."""
    text = path.read_text()
    parts = text.split("---", 2)
    assert len(parts) >= 3, f"Invalid frontmatter in {path}"
    fm = yaml.safe_load(parts[1])
    body = parts[2].lstrip("\n")
    return fm, body


def _is_empty(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, (str, list, dict)) and not v:
        return True
    return False


def _harness_fields(fm: Dict, harness: str, valid: Set[str]) -> Dict[str, Any]:
    """Extract non-null fields from a harness block."""
    block = fm.get(harness) or {}
    return {k: v for k, v in block.items() if k in valid and not _is_empty(v)}

# ---------------------------------------------------------------------------
# Emitters
# ---------------------------------------------------------------------------


def _emit_md(fields: Dict[str, Any], body: str) -> str:
    """Emit a harness agent .md file (Claude Code or Pi)."""
    out = dict(fields)
    if "description" in out:
        out["description"] = _Folded(out["description"])
    fm = yaml.dump(
        out,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    ).rstrip()
    return f"---\n{fm}\n---\n\n{body}"


def _esc_toml(s: str) -> str:
    """Escape for a TOML basic (double-quoted) string."""
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
        .strip()
    )


def _toml_kv(k: str, v: Any) -> str:
    """Format one TOML key = value."""
    if isinstance(v, bool):
        return f"{k} = {'true' if v else 'false'}"
    if isinstance(v, (int, float)):
        return f"{k} = {v}"
    if isinstance(v, list):
        items = ", ".join(f'"{_esc_toml(str(i))}"' for i in v)
        return f"{k} = [{items}]"
    return f'{k} = "{_esc_toml(str(v))}"'


def _esc_toml_multiline(s: str) -> str:
    """Escape for a TOML multiline basic string (triple-quoted)."""
    return s.replace("\\", "\\\\").replace('"""', '""\\"')


def _emit_toml(
    name: str, description: str, body: str, extra: Dict[str, Any]
) -> str:
    """Emit a Codex agent .toml file."""
    safe_body = _esc_toml_multiline(body)
    lines = [
        "# generated by harness_sync from ~/.agents/ — do not edit directly",
        f'name = "{_esc_toml(name)}"',
        f'description = "{_esc_toml(description)}"',
        f'developer_instructions = """\n{safe_body}"""',
    ]
    for k, v in extra.items():
        lines.append(_toml_kv(k, v))
    return "\n".join(lines) + "\n"

# ---------------------------------------------------------------------------
# Symlink helper
# ---------------------------------------------------------------------------


def _ensure_symlink(source: Path, target: Path) -> Optional[str]:
    """Create symlink target -> source. Returns error string or None."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        if target.resolve() == source.resolve():
            return None
        target.unlink()
    elif target.exists():
        if not FORCE:
            return f"{target}: exists and is not a symlink, skipping (use --force)"
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    target.symlink_to(source)
    return None

# ---------------------------------------------------------------------------
# Machine detection — customize for your machines
# ---------------------------------------------------------------------------


def _detect_machine() -> str:
    """Detect the current machine from hostname.

    Customize this function for your environment. Map hostname patterns
    to short machine names that match keys in projects/main.yml.
    """
    hostname = socket.gethostname()
    # Example mappings — replace with your own:
    # if hostname == "my-laptop":
    #     return "laptop"
    # if hostname.startswith("gpu-node"):
    #     return "cluster"
    return hostname

# ---------------------------------------------------------------------------
# Deploy: instructions (global user instructions)
# ---------------------------------------------------------------------------


def deploy_instructions() -> Tuple[List[str], List[str]]:
    """Deploy INSTRUCTIONS.md to all harnesses."""
    deployed: List[str] = []
    errors: List[str] = []
    src = REPO / "INSTRUCTIONS.md"
    if not src.exists():
        return deployed, ["INSTRUCTIONS.md not found"]

    src_rel = str(src.relative_to(HOME))
    for target in [CLAUDE_INSTRUCTIONS, PI_INSTRUCTIONS]:
        err = _ensure_symlink(src, target)
        if err:
            errors.append(err)
        else:
            deployed.append(f"~/{src_rel} → ~/{target.relative_to(HOME)}")

    return deployed, errors

# ---------------------------------------------------------------------------
# Deploy: agents
# ---------------------------------------------------------------------------


def deploy_agents() -> Tuple[List[str], List[str]]:
    """Deploy canonical agents to all harnesses. Returns (deployed, errors)."""
    deployed: List[str] = []
    errors: List[str] = []
    src = REPO / "agents"
    if not src.is_dir():
        return deployed, ["agents/ directory not found"]

    for path in sorted(src.glob("*.md")):
        name = path.stem
        if name in SKIP_AGENTS:
            continue
        try:
            fm, body = parse_agent(path)
        except Exception as e:
            errors.append(f"{name}: parse error — {e}")
            continue

        desc = fm.get("description", "")

        # Claude Code
        cf = {"name": name, "description": desc}
        cf.update(_harness_fields(fm, "claude", CLAUDE_FIELDS))
        t = CLAUDE_AGENTS / f"{name}.md"
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_text(_emit_md(cf, body))

        # Pi
        pf = {"name": name, "description": desc}
        pf.update(_harness_fields(fm, "pi", PI_FIELDS))
        t = PI_AGENTS / f"{name}.md"
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_text(_emit_md(pf, body))

        # Codex
        cx = _harness_fields(fm, "codex", CODEX_FIELDS)
        t = CODEX_AGENTS / f"{name}.toml"
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_text(_emit_toml(name, desc, body, cx))

        deployed.append(name)

    return deployed, errors

# ---------------------------------------------------------------------------
# Deploy: skills (symlinks)
# ---------------------------------------------------------------------------


def _copy_skills(src: Path, dest: Path) -> None:
    """Copy skill directories from src to dest, skipping .system/.

    Codex writes .system/ into the skills directory, so we copy instead
    of symlinking to isolate the canonical source from Codex mutations.
    """
    # Replace stale symlink with a real directory
    if dest.is_symlink():
        dest.unlink()
    dest.mkdir(parents=True, exist_ok=True)
    for item in sorted(src.iterdir()):
        if item.name.startswith("."):
            continue
        target = dest / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def deploy_skills() -> Tuple[List[str], List[str]]:
    """Deploy skills: symlink for Claude/Pi, copy for Codex."""
    deployed: List[str] = []
    errors: List[str] = []
    src = REPO / "skills"
    if not src.is_dir():
        return deployed, ["skills/ directory not found"]

    # Claude + Pi: symlink (edits take effect immediately)
    src_rel = str(src.relative_to(HOME))
    for target in [CLAUDE_SKILLS, PI_SKILLS]:
        err = _ensure_symlink(src, target)
        if err:
            errors.append(err)
        else:
            deployed.append(f"~/{src_rel} → ~/{target.relative_to(HOME)}")

    # Codex: copy (isolates canonical source from Codex .system/ writes)
    _copy_skills(src, CODEX_SKILLS)
    deployed.append(f"~/{src_rel} → ~/{CODEX_SKILLS.relative_to(HOME)} (copy)")

    return deployed, errors

# ---------------------------------------------------------------------------
# Deploy: rules
# ---------------------------------------------------------------------------


def _collect_rule_files() -> List[Path]:
    """Return sorted list of rule .md files, or empty list."""
    rules_dir = REPO / "rules"
    if not rules_dir.is_dir():
        return []
    return sorted(f for f in rules_dir.rglob("*.md") if f.stem != "README")


def _compile_rules(files: List[Path], base: Path) -> str:
    """Concatenate rules into a single string with section headers."""
    sections = []
    for f in files:
        rel = f.relative_to(base)
        content = f.read_text().rstrip()
        sections.append(f"# {rel}\n\n{content}")
    return "\n\n---\n\n".join(sections)


def _update_codex_config(
    rules_content: str,
    config_path: Path = CODEX_CONFIG,
    instructions_content: Optional[str] = None,
) -> None:
    """Write instructions + rules into the `instructions` key of config.toml.

    Uses markers so the script only touches its own section. Other keys
    in config.toml are preserved.
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    marker_s = "# --- BEGIN harness_sync ---"
    marker_e = "# --- END harness_sync ---"
    parts = []
    if instructions_content:
        parts.append(instructions_content.rstrip())
    if rules_content:
        parts.append(rules_content.rstrip())
    combined = "\n\n---\n\n".join(parts)
    safe = _esc_toml_multiline(combined)
    block = (
        f"{marker_s}\n"
        f'instructions = """\n{safe}\n"""\n'
        f"{marker_e}"
    )

    if not config_path.exists():
        config_path.write_text(block + "\n")
        return

    text = config_path.read_text()
    # Remove legacy marker block (renamed from "harness_sync rules")
    old_s = "# --- BEGIN harness_sync rules ---"
    old_e = "# --- END harness_sync rules ---"
    old_pat = re.escape(old_s) + r"[\s\S]*?" + re.escape(old_e) + r"\n*"
    text = re.sub(old_pat, "", text)
    # Replace or append current marker block
    pat = re.escape(marker_s) + r"[\s\S]*?" + re.escape(marker_e)
    if re.search(pat, text):
        text = re.sub(pat, lambda _: block, text)
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    config_path.write_text(text)


def deploy_rules() -> Tuple[List[str], List[str]]:
    """Deploy rules to all harnesses."""
    deployed: List[str] = []
    errors: List[str] = []
    rules_dir = REPO / "rules"
    files = _collect_rule_files()
    if not files:
        return deployed, []

    # Claude + Pi: symlink entire rules directory
    src_rel = str(rules_dir.relative_to(HOME))
    for target in [CLAUDE_RULES, PI_RULES]:
        err = _ensure_symlink(rules_dir, target)
        if err:
            errors.append(err)
        else:
            deployed.append(f"~/{src_rel} → ~/{target.relative_to(HOME)}")

    # Codex: compile instructions + rules into config.toml
    compiled = _compile_rules(files, rules_dir)
    instructions_src = REPO / "INSTRUCTIONS.md"
    instructions_text = (
        instructions_src.read_text().rstrip() if instructions_src.exists() else None
    )
    _update_codex_config(compiled, instructions_content=instructions_text)
    has_instructions = instructions_text is not None
    label = f"instructions + {len(files)} rules" if has_instructions else f"{len(files)} rules"
    deployed.append(f"codex/config.toml ({label})")

    return deployed, errors

# ---------------------------------------------------------------------------
# Deploy: Claude Code config (settings, hooks)
# ---------------------------------------------------------------------------


def deploy_claude_config() -> Tuple[List[str], List[str]]:
    """Deploy Claude Code settings.json, settings.local.json, and hooks."""
    deployed: List[str] = []
    errors: List[str] = []
    claude_src = REPO / "claude"
    if not claude_src.is_dir():
        return deployed, []

    # settings.json
    src_settings = claude_src / "settings.json"
    if src_settings.exists():
        err = _ensure_symlink(src_settings, CLAUDE_SETTINGS)
        if err:
            errors.append(err)
        else:
            deployed.append("settings.json")

    # settings.local.json
    src_local = claude_src / "settings.local.json"
    if src_local.exists():
        err = _ensure_symlink(src_local, CLAUDE_SETTINGS_LOCAL)
        if err:
            errors.append(err)
        else:
            deployed.append("settings.local.json")

    # hooks/ directory
    src_hooks = claude_src / "hooks"
    if src_hooks.is_dir():
        err = _ensure_symlink(src_hooks, CLAUDE_HOOKS)
        if err:
            errors.append(err)
        else:
            deployed.append("hooks/")

    # .mcp.json
    src_mcp = claude_src / ".mcp.json"
    if src_mcp.exists():
        err = _ensure_symlink(src_mcp, CLAUDE_MCP)
        if err:
            errors.append(err)
        else:
            deployed.append(".mcp.json")

    return deployed, errors

# ---------------------------------------------------------------------------
# Deploy: Pi config (settings, mcp, extensions)
# ---------------------------------------------------------------------------


def deploy_pi_config() -> Tuple[List[str], List[str]]:
    """Symlink everything in ~/.agents/pi/ to ~/.pi/ or ~/.pi/agent/."""
    deployed: List[str] = []
    errors: List[str] = []
    pi_src = REPO / "pi"
    if not pi_src.is_dir():
        return deployed, []

    for item in sorted(pi_src.iterdir()):
        if item.name.startswith("."):
            continue
        parent = PI_ROOT if item.name in PI_ROOT_ITEMS else PI_DEPLOY
        target = parent / item.name
        err = _ensure_symlink(item, target)
        if err:
            errors.append(err)
        else:
            suffix = "/" if item.is_dir() else ""
            rel = f"~/{target.relative_to(HOME)}"
            deployed.append(f"{item.name}{suffix} → {rel}")

    return deployed, errors

# ---------------------------------------------------------------------------
# Deploy: projects
# ---------------------------------------------------------------------------

def deploy_projects() -> Tuple[List[str], List[str]]:
    """Deploy project-scoped configs."""
    deployed: List[str] = []
    errors: List[str] = []
    projects_file = REPO / "projects" / "main.yml"
    if not projects_file.exists():
        return deployed, ["projects/main.yml not found"]

    machine = _detect_machine()
    projects = yaml.safe_load(projects_file.read_text()) or {}
    rule_files = _collect_rule_files()

    for proj_name, machine_paths in projects.items():
        if not isinstance(machine_paths, dict):
            continue
        if machine not in machine_paths:
            continue
        proj_path = Path(machine_paths[machine])
        if not proj_path.is_dir():
            errors.append(f"{proj_name}: {proj_path} does not exist on {machine}")
            continue

        proj_src = REPO / "projects" / proj_name
        if not proj_src.is_dir():
            continue

        # --- Instruction file -> CLAUDE.md + AGENTS.md (symlink) ---
        instructions_md = proj_src / "INSTRUCTIONS.md"
        proj_instructions_text: Optional[str] = None
        if instructions_md.exists():
            proj_instructions_text = instructions_md.read_text().rstrip()
            for target in [proj_path / "CLAUDE.md", proj_path / "AGENTS.md"]:
                err = _ensure_symlink(instructions_md, target)
                if err:
                    errors.append(err)
            deployed.append(f"{proj_name}: CLAUDE.md + AGENTS.md")

        # --- Project skills (symlink for Claude/Pi, copy for Codex) ---
        proj_skills = proj_src / "skills"
        if proj_skills.is_dir():
            for sd in sorted(proj_skills.iterdir()):
                if not sd.is_dir() or sd.name.startswith("."):
                    continue
                for tp in [
                    proj_path / ".claude" / "skills",
                    proj_path / ".pi" / "skills",
                ]:
                    err = _ensure_symlink(sd, tp / sd.name)
                    if err:
                        errors.append(err)
                codex_skill = proj_path / ".codex" / "skills" / sd.name
                codex_skill.parent.mkdir(parents=True, exist_ok=True)
                if codex_skill.is_symlink():
                    codex_skill.unlink()
                elif codex_skill.exists():
                    shutil.rmtree(codex_skill)
                shutil.copytree(sd, codex_skill)
                deployed.append(f"{proj_name}: skill {sd.name}")

        # --- Project agents (harness-specific transforms) ---
        proj_agents = proj_src / "agents"
        if proj_agents.is_dir():
            for af in sorted(proj_agents.glob("*.md")):
                name = af.stem
                if name in SKIP_AGENTS:
                    continue
                try:
                    fm, body = parse_agent(af)
                except Exception as e:
                    errors.append(f"{proj_name}/{name}: parse error — {e}")
                    continue
                desc = fm.get("description", "")

                # Claude
                cf = {"name": name, "description": desc}
                cf.update(_harness_fields(fm, "claude", CLAUDE_FIELDS))
                t = proj_path / ".claude" / "agents" / f"{name}.md"
                t.parent.mkdir(parents=True, exist_ok=True)
                t.write_text(_emit_md(cf, body))

                # Pi
                pf = {"name": name, "description": desc}
                pf.update(_harness_fields(fm, "pi", PI_FIELDS))
                t = proj_path / ".pi" / "agents" / f"{name}.md"
                t.parent.mkdir(parents=True, exist_ok=True)
                t.write_text(_emit_md(pf, body))

                # Codex
                cx = _harness_fields(fm, "codex", CODEX_FIELDS)
                t = proj_path / ".codex" / "agents" / f"{name}.toml"
                t.parent.mkdir(parents=True, exist_ok=True)
                t.write_text(_emit_toml(name, desc, body, cx))

                deployed.append(f"{proj_name}: agent {name}")

        # --- Project-level Claude config (settings, hooks) ---
        proj_claude = proj_src / "claude"
        if proj_claude.is_dir():
            # settings.local.json
            src_local = proj_claude / "settings.local.json"
            if src_local.exists():
                err = _ensure_symlink(
                    src_local,
                    proj_path / ".claude" / "settings.local.json",
                )
                if err:
                    errors.append(err)
                else:
                    deployed.append(f"{proj_name}: settings.local.json")

            # hooks/
            src_hooks = proj_claude / "hooks"
            if src_hooks.is_dir():
                err = _ensure_symlink(
                    src_hooks,
                    proj_path / ".claude" / "hooks",
                )
                if err:
                    errors.append(err)
                else:
                    deployed.append(f"{proj_name}: hooks/")

        # --- Project-level rules (symlinked to <project>/.claude/rules/) ---
        proj_rules = proj_src / "rules"
        if proj_rules.is_dir():
            proj_rule_files = sorted(
                f for f in proj_rules.rglob("*.md") if f.stem != "README"
            )
            if proj_rule_files:
                for target in [
                    proj_path / ".claude" / "rules",
                    proj_path / ".pi" / "rules",
                ]:
                    err = _ensure_symlink(proj_rules, target)
                    if err:
                        errors.append(err)
                deployed.append(
                    f"{proj_name}: project rules ({len(proj_rule_files)} files)"
                )

        # --- Codex: compile global + project rules into config.toml ---
        rules_dir = REPO / "rules"
        proj_rules_dir = proj_src / "rules"
        all_rule_sections = []
        if rule_files:
            all_rule_sections.append(_compile_rules(rule_files, rules_dir))
        proj_rule_files_for_codex = []
        if proj_rules_dir.is_dir():
            proj_rule_files_for_codex = sorted(
                f for f in proj_rules_dir.rglob("*.md") if f.stem != "README"
            )
        if proj_rule_files_for_codex:
            all_rule_sections.append(
                _compile_rules(proj_rule_files_for_codex, proj_rules_dir)
            )
        if all_rule_sections:
            combined_rules = "\n\n---\n\n".join(all_rule_sections)
            _update_codex_config(
                combined_rules, proj_path / ".codex" / "config.toml",
                instructions_content=proj_instructions_text,
            )
            nb_global = len(rule_files)
            nb_proj = len(proj_rule_files_for_codex)
            deployed.append(
                f"{proj_name}: codex config "
                f"({nb_global} global + {nb_proj} project rules)"
            )

    return deployed, errors

# ---------------------------------------------------------------------------
# Flag unmanaged files
# ---------------------------------------------------------------------------


def flag_unmanaged() -> Dict[str, List[str]]:
    """Find unmanaged files in deploy targets. Delete them if CLEAN is set."""
    managed_agents = {
        p.stem for p in (REPO / "agents").glob("*.md")
    } - SKIP_AGENTS
    managed_skills: Set[str] = set()
    if (REPO / "skills").is_dir():
        managed_skills = {
            p.name for p in (REPO / "skills").iterdir() if p.is_dir()
        }

    unmanaged: Dict[str, List[str]] = {}

    def _scan_agents(directory: Path, ext: str) -> None:
        if not directory.is_dir():
            return
        for f in directory.glob(f"*{ext}"):
            if f.stem not in managed_agents and f.stem != "README":
                unmanaged.setdefault(str(directory) + "/", []).append(f.name)
                if CLEAN:
                    f.unlink()

    def _scan_skills(directory: Path) -> None:
        if not directory.is_dir():
            return
        for d in directory.iterdir():
            if d.is_dir() and d.name not in managed_skills:
                unmanaged.setdefault(str(directory) + "/", []).append(d.name)
                if CLEAN:
                    shutil.rmtree(d)

    _scan_agents(CLAUDE_AGENTS, ".md")
    _scan_agents(PI_AGENTS, ".md")
    _scan_agents(CODEX_AGENTS, ".toml")
    _scan_skills(CLAUDE_SKILLS)
    _scan_skills(PI_SKILLS)
    _scan_skills(CODEX_SKILLS)

    return unmanaged

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print("harness_sync: deploying from ~/.agents/\n")
    has_errors = False

    # Instructions
    deployed, errors = deploy_instructions()
    if deployed:
        print(f"Instructions: symlinked -> {len(deployed)} targets")
        for d in deployed:
            print(f"  {d}")
    if errors:
        has_errors = True
        for e in errors:
            print(f"  ERROR: {e}")

    # Agents
    deployed, errors = deploy_agents()
    if deployed:
        print(f"\nAgents: {len(deployed)} built -> claude, pi, codex")
        for n in deployed:
            print(f"  {n}")
    if errors:
        has_errors = True
        for e in errors:
            print(f"  ERROR: {e}")

    # Skills
    deployed, errors = deploy_skills()
    if deployed:
        print(f"\nSkills: {len(deployed)} symlinked -> claude, pi, codex")
        for n in deployed:
            print(f"  {n}")
    if errors:
        has_errors = True
        for e in errors:
            print(f"  ERROR: {e}")

    # Claude config
    deployed, errors = deploy_claude_config()
    if deployed:
        print(f"\nClaude config: {len(deployed)} items symlinked")
        for d in deployed:
            print(f"  {d}")
    if errors:
        has_errors = True
        for e in errors:
            print(f"  ERROR: {e}")

    # Pi config
    deployed, errors = deploy_pi_config()
    if deployed:
        print(f"\nPi config: {len(deployed)} items symlinked")
        for d in deployed:
            print(f"  {d}")
    if errors:
        has_errors = True
        for e in errors:
            print(f"  ERROR: {e}")

    # Rules
    deployed, errors = deploy_rules()
    if deployed:
        print(f"\nRules: {len(deployed)} symlinked")
        for d in deployed:
            print(f"  {d}")
    elif not _collect_rule_files():
        print("\nRules: none found (rules/ empty)")
    if errors:
        has_errors = True
        for e in errors:
            print(f"  ERROR: {e}")

    # Projects
    deployed, errors = deploy_projects()
    if deployed:
        print(f"\nProjects: {len(deployed)} deployments")
        for d in deployed:
            print(f"  {d}")
    if errors:
        has_errors = True
        for e in errors:
            print(f"  ERROR: {e}")

    # Unmanaged
    unmanaged = flag_unmanaged()
    if unmanaged:
        verb = "Cleaned" if CLEAN else "Unmanaged"
        print(f"\n{verb} (not in ~/.agents/):")
        for loc, files in sorted(unmanaged.items()):
            for f in sorted(files):
                print(f"  {loc}{f}")

    print()
    return 1 if has_errors else 0


if __name__ == "__main__":
    if "--force" in sys.argv:
        FORCE = True
    if "--clean" in sys.argv:
        CLEAN = True
    sys.exit(main())
