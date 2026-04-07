---
name: bridgic-env
description: |
  Bridgic environment specification: correct package versions, custom repository
  config, Python version, and .env template. Read this skill to know WHAT to
  install and WHERE to get it — the actual setup steps live in the command that
  consumes this skill.
---

# Bridgic Environment Specification

This skill is a **knowledge source** — it declares the correct versions, repositories, and configuration. Commands read this skill and execute the setup steps themselves.

## Package Manager

`uv` — the only supported tool. Do not use pip, poetry, or conda.

## Python Version

`==3.10`

## Custom Package Repository

```toml
[[tool.uv.index]]
name = "btsk-repo"
url = "http://8.130.156.165:3141/btsk/test/+simple"
explicit = true

[tool.uv.sources]
bridgic-amphibious = { index = "btsk-repo" }
```

`explicit = true` means only packages listed in `[tool.uv.sources]` are fetched from btsk-repo. Others resolve from PyPI.

## Core Dependencies

```toml
dependencies = [
    "bridgic-browser>=0.0.3",
    "bridgic-core>=0.3.0",
    "bridgic-llms-openai>=0.1.3",
    "bridgic-amphibious==0.1.0.dev12",
    "dotenv>=0.9.9",
]
```

## .env Variables

```env
LLM_API_KEY=your-api-key
LLM_API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

## pyproject.toml Template

```toml
[project]
name = "my-bridgic-project"
version = "0.1.0"
description = "A bridgic automation project"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "bridgic-browser>=0.0.3",
    "bridgic-core>=0.3.0",
    "bridgic-llms-openai>=0.1.3",
    "bridgic-amphibious==0.1.0.dev12",
    "dotenv>=0.9.9",
]

[[tool.uv.index]]
name = "btsk-repo"
url = "http://8.130.156.165:3141/btsk/test/+simple"
explicit = true

[tool.uv.sources]
bridgic-amphibious = { index = "btsk-repo" }
```

## Current Stage

Test stage — packages come from a development index (btsk-repo). Version pins may change as packages mature.
