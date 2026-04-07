# Bridgic Corpus

Agent skill & knowledge corpus for the Bridgic ecosystem — providing skills, agents, and commands for building high-quality bridgic projects. Skills cover the foundational specs; commands and agents orchestrate them into end-to-end workflows.

## Architecture

```
bridgic-corpus/
├── CLAUDE.md                          ← this file
├── .claude-plugin/
│   └── plugin.json                    ← Claude Code plugin registration
├── skills/                            ← domain knowledge: "what it is, how to use it"
│   ├── bridgic-browser/               ← browser automation CLI + SDK
│   ├── bridgic-amphibious/            ← dual-mode agent framework
│   ├── bridgic-llms/                  ← LLM providers and initialization
│   └── bridgic-env/                   ← environment setup (uv, deps, .env)
├── agents/                            ← execution methodology: "how to do it well"
│   ├── browser-explorer.md            ← CLI exploration expertise
│   ├── amphibious-generator.md        ← code generation expertise
│   └── amphibious-verify.md           ← project verification expertise
├── commands/                          ← user-invocable workflows (thin orchestrators)
│   ├── browser-to-amphibious.md       ← /browser-to-amphibious pipeline
│   └── references/
│       └── browser-code-patterns.md   ← browser-specific code patterns
├── hooks/                             ← auto-loaded by Claude Code
│   ├── hooks.json                     ← hook definitions
│   └── README.md                      ← hook system documentation
└── scripts/                           ← hook and utility implementations
    ├── hook/                          ← hook script implementations
    │   └── inject-plugin-root.sh      ← injects BRIDGIC_PLUGIN_ROOT into subagent prompts
    └── run/                           ← runtime utility scripts
        └── monitor.sh                 ← process monitor for amphibious-verify agent
```

### Component Roles

| Type | Purpose | Example |
|------|---------|---------|
| **Skill** | Domain knowledge reference — loaded on-demand by agents | bridgic-browser, bridgic-amphibious, bridgic-llms, bridgic-env |
| **Agent** | Deep execution methodology — delegated by commands | browser-explorer, amphibious-generator, amphibious-verify |
| **Command** | Multi-step orchestrator invoked by user | /browser-to-amphibious |

## Installation

```bash
# Register marketplace (one-time), then install
claude plugin marketplace add bitsky-tech/bridgic-corpus
claude plugin install bridgic-corpus
```

## Skills

| Skill | When to Use |
|-------|-------------|
| **bridgic-browser** | Browser automation via CLI (`bridgic-browser ...`) or Python SDK (`from bridgic.browser`) |
| **bridgic-amphibious** | Building dual-mode agents with `AmphibiousAutoma`, `CognitiveWorker`, `on_agent`/`on_workflow` |
| **bridgic-llms** | Initializing LLM providers (`OpenAILlm`, `OpenAILikeLlm`, `VllmServerLlm`), configuring `OpenAIConfiguration` |
| **bridgic-env** | Setting up a bridgic project environment (uv, dependencies, custom repo, .env) |

## Agents

| Agent | When to Use |
|-------|-------------|
| **browser-explorer** | Systematically explore a website via CLI, produce structured exploration report |
| **amphibious-generator** | Generate a complete bridgic-amphibious project from a task description with optional domain context |
| **amphibious-verify** | Verify a generated amphibious project: inject debug instrumentation, run with monitoring, validate results, clean up |

## Commands

| Command | When to Use |
|---------|-------------|
| **/browser-to-amphibious** | Turn a browser task into a working bridgic-amphibious project (parse → explore → generate → verify) |
