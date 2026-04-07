#!/bin/bash
# Inject BRIDGIC_PLUGIN_ROOT into Agent tool prompts.
# Subagents don't inherit plugin context, so they can't find skill files.
# This hook appends the plugin root and file conventions to the end of
# every bridgic Agent prompt, enabling direct Read access to skill references.
#
# Pure bash + awk — no dependency on python, node, jq, or any runtime.

INPUT=$(cat)
ROOT="${CLAUDE_PLUGIN_ROOT:-}"

# No plugin root available — pass through unchanged
if [ -z "$ROOT" ]; then
  printf '{}'
  exit 0
fi

# Build match pattern from agent filenames in this plugin (auto-discovers new agents)
MATCH_PATTERN=""
if [ -d "$ROOT/agents" ]; then
  for f in "$ROOT"/agents/*.md; do
    [ -f "$f" ] || continue
    name=$(basename "$f" .md)
    MATCH_PATTERN="${MATCH_PATTERN:+$MATCH_PATTERN|}$name"
  done
fi
# Add "bridgic" as fallback keyword
MATCH_PATTERN="${MATCH_PATTERN:+$MATCH_PATTERN|}bridgic"

# Not a bridgic agent — pass through unchanged
if ! printf '%s' "$INPUT" | grep -qiE "$MATCH_PATTERN"; then
  printf '{}'
  exit 0
fi

# Escape root path for safe embedding in awk (handle backslashes and quotes)
SAFE_ROOT=$(printf '%s' "$ROOT" | sed 's/\\/\\\\/g; s/"/\\"/g')

printf '%s' "$INPUT" | awk -v root="$SAFE_ROOT" '
{
  # Concatenate all lines into one string (handle both single-line and pretty-printed JSON)
  full = full (NR > 1 ? "\n" : "") $0
}
END {
  # Build concise injection text (appended at end of prompt)
  inj = "\\n\\n---\\n\\n"
  inj = inj "BRIDGIC_PLUGIN_ROOT=" root "\\n"
  inj = inj "Skill: {BRIDGIC_PLUGIN_ROOT}/skills/<name>/SKILL.md | references/<file>.md\\n"
  inj = inj "Command ref: {BRIDGIC_PLUGIN_ROOT}/commands/references/<file>.md\\n"
  inj = inj "Read directly. Do not search."

  # Find the prompt string value and append injection before its closing quote
  if (match(full, /"prompt"[ \t]*:[ \t]*"/)) {
    start = RSTART + RLENGTH
    # Scan through the prompt string value to find its closing quote
    esc = 0; end_pos = 0
    for (i = start; i <= length(full); i++) {
      c = substr(full, i, 1)
      if (esc) { esc = 0; continue }
      if (c == "\\") { esc = 1; continue }
      if (c == "\"") { end_pos = i; break }
    }
    if (end_pos > 0) {
      full = substr(full, 1, end_pos - 1) inj substr(full, end_pos)
    } else {
      printf "{}"
      exit 0
    }
  } else {
    # No prompt field — cannot inject, pass through
    printf "{}"
    exit 0
  }

  # Extract tool_input object via brace matching (string-aware)
  if (match(full, /"tool_input"[ \t]*:[ \t]*/)) {
    start = RSTART + RLENGTH
    rest = substr(full, start)

    depth = 0; in_str = 0; esc = 0; result = ""
    for (i = 1; i <= length(rest); i++) {
      c = substr(rest, i, 1)
      result = result c

      if (esc)    { esc = 0; continue }
      if (c == "\\") { esc = 1; continue }
      if (c == "\"") { in_str = !in_str; continue }
      if (in_str) continue
      if (c == "{") depth++
      if (c == "}") { depth--; if (depth == 0) break }
    }

    printf "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"allow\",\"updatedInput\":%s}}", result
  } else {
    printf "{}"
  }
}' 2>/dev/null || printf '{}'
