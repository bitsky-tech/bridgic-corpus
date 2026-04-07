# Hooks

Hooks are event-driven automations that fire before or after Claude Code tool executions. In this plugin, hooks solve infrastructure concerns that should not pollute skill, agent, or command content.

## How Hooks Work

```
User request → Claude picks a tool → PreToolUse hook runs → Tool executes → PostToolUse hook runs
```

- **PreToolUse** hooks run before the tool executes. They can **block** (exit code 2), **warn** (stderr), or **modify tool input** (`updatedInput`).
- **PostToolUse** hooks run after the tool completes. They can analyze output but cannot block.
- **Stop** hooks run after each Claude response.

Claude Code automatically loads `hooks/hooks.json` from any installed plugin — no registration in `plugin.json` required.

## Hooks in This Plugin

### PreToolUse Hooks

| Hook | Matcher | What It Does | Script |
|------|---------|-------------|--------|
| **Plugin root injection** | `Agent` | Injects `BRIDGIC_PLUGIN_ROOT` into subagent prompts so they can locate skill files without searching the filesystem | `scripts/hook/inject-plugin-root.sh` |

### Why Plugin Root Injection?

Subagents spawned via the Agent tool do **not** inherit the plugin's context — they cannot discover skill files on their own. Without this hook, subagents resort to `find` commands across the home directory, wasting time and risking interference from unrelated files.

The hook solves this by appending the plugin root path and file location conventions to the end of the subagent's prompt via `updatedInput`:

```
---
BRIDGIC_PLUGIN_ROOT=/absolute/path/to/bridgic
Skill: {BRIDGIC_PLUGIN_ROOT}/skills/<name>/SKILL.md | references/<file>.md
Command ref: {BRIDGIC_PLUGIN_ROOT}/commands/references/<file>.md
Read directly. Do not search.
```

This keeps agent and command files focused on methodology — they only declare **what** skills they depend on, not **how** to find them.

## Adding a New Hook

1. Write the script in the appropriate `scripts/` subdirectory:
   - `scripts/hook/` — hook script implementations (e.g., plugin root injection)
   - `scripts/<domain>/` — domain-specific hooks (create as needed)

2. Register it in `hooks.json`:

```json
{
  "matcher": "ToolName",
  "hooks": [
    {
      "type": "command",
      "command": "bash \"${CLAUDE_PLUGIN_ROOT}/scripts/<subdir>/<script>.sh\""
    }
  ],
  "description": "What this hook does"
}
```

3. `${CLAUDE_PLUGIN_ROOT}` is automatically set by Claude Code to the plugin's root directory.

## Hook Script Conventions

- **Input**: JSON on stdin (tool name, tool input, session info)
- **Output**: JSON on stdout
- **Exit codes**: `0` = success, `2` = block (PreToolUse only), other non-zero = error (logged, does not block)
- **Error handling**: Always exit `0` on non-critical failures — never block tool execution unexpectedly
- **Stderr**: Use for warnings visible to Claude but non-blocking

## Related

- [scripts/hook/](../scripts/hook/) — Hook script implementations
- [CLAUDE.md](../CLAUDE.md) — Plugin architecture overview
