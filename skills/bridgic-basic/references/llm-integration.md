# LLM Integration

How to use LLMs with Bridgic, including Message construction, Response handling, structured output, and streaming.

## Message Construction

`Message` does **NOT** accept `content` as a constructor parameter. Use factory methods:

```python
from bridgic.core.model.types import Message, Role

# CORRECT: Use factory methods
msg = Message.from_text("Hello", role=Role.USER)
system_msg = Message.from_text("You are a helpful assistant.", role=Role.SYSTEM)

# WRONG: content is NOT a constructor parameter
# msg = Message(role=Role.USER, content="Hello")  # This will FAIL!
```

## Message Properties

- `message.content` — property that joins all TextBlock texts with `"\n\n"`
- `message.blocks` — raw list of ContentBlock (TextBlock, ToolCallBlock, ToolResultBlock)
- `message.role` — Role enum value

## Role Enum

```python
from bridgic.core.model.types import Role

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    AI = "assistant"   # NOTE: string value is "assistant", not "ai"
    TOOL = "tool"
```

## Response Object

`achat()` / `chat()` returns a `Response`, NOT a Message directly:

```python
from bridgic.core.model.types import Response

response: Response = await llm.achat(messages=[...])

# Response fields:
#   response.message: Optional[Message]  — the structured message
#   response.raw: Optional[Any]          — raw provider response

# CORRECT: Access text via message.content
text = response.message.content

# WRONG: Response has no .content attribute
# text = response.content  # AttributeError!
```

## LLM Providers

Bridgic ships three LLM integrations. Install only what you need.

### OpenAILlm — Official OpenAI API

```shell
pip install bridgic-llms-openai
```

```python
from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration

# Minimal — uses OpenAI default endpoint
llm = OpenAILlm(
    api_key="your-api-key",
    configuration=OpenAIConfiguration(model="gpt-4o"),
)

# Full constructor — all parameters
llm = OpenAILlm(
    api_key="your-api-key",          # Required. OpenAI API key.
    api_base=None,                   # Optional[str]. Custom endpoint URL (e.g. Azure OpenAI).
                                     #   If None, uses the default OpenAI endpoint.
    configuration=OpenAIConfiguration(
        model="gpt-4o",              # Default model; can be overridden per call.
        temperature=0.7,             # Sampling temperature [0, 2]. Default: None (provider default).
        top_p=None,                  # Nucleus sampling (0, 1]. Alternative to temperature.
        presence_penalty=None,       # [-2.0, 2.0]. Penalise tokens that have appeared so far.
        frequency_penalty=None,      # [-2.0, 2.0]. Penalise tokens by their frequency so far.
        max_tokens=None,             # Max tokens to generate.
        stop=None,                   # List[str]. Up to 4 stop sequences.
    ),
    timeout=30.0,                    # Optional[float]. Request timeout in seconds.
    http_client=None,                # Optional[httpx.Client]. Custom sync HTTP client.
    http_async_client=None,          # Optional[httpx.AsyncClient]. Custom async HTTP client.
)
```

`OpenAILlm` supports **all** LLM methods: `chat`/`achat`, `stream`/`astream`, `select_tool`/`aselect_tool`, `structured_output`/`astructured_output`.

---

### OpenAILikeLlm — Third-party OpenAI-compatible APIs

For providers that expose an OpenAI-compatible API (e.g. DeepSeek, Moonshot, Groq, local Ollama).

```shell
pip install bridgic-llms-openai-like
```

```python
from bridgic.llms.openai_like import OpenAILikeLlm, OpenAILikeConfiguration

llm = OpenAILikeLlm(
    api_base="https://api.deepseek.com/v1",   # Required. Provider endpoint URL.
    api_key="your-api-key",                   # Required.
    configuration=OpenAILikeConfiguration(
        model="deepseek-chat",
        temperature=0.7,
    ),
    timeout=60.0,
)
```

> **Limitation:** `OpenAILikeLlm` only supports `chat`/`achat` and `stream`/`astream`. It does NOT support `structured_output` or `select_tool`.

---

### VllmServerLlm — Self-hosted vLLM

For self-hosted models served via the vLLM inference engine (OpenAI-compatible API + vLLM extras).

```shell
pip install bridgic-llms-vllm
```

```python
from bridgic.llms.vllm import VllmServerLlm, VllmServerConfiguration

llm = VllmServerLlm(
    api_base="http://localhost:8000/v1",   # Required. vLLM server URL.
    api_key="token-abc123",               # Required (any non-empty string if auth disabled).
    configuration=VllmServerConfiguration(
        model="meta-llama/Llama-3-8b-instruct",
        temperature=0.8,
        max_tokens=512,
    ),
    timeout=120.0,
)
```

`VllmServerLlm` supports all methods including `structured_output` and `select_tool`.

---

### Configuration Fields Reference

All three providers share the same configuration field set (`OpenAILikeConfiguration` is the base):

| Field | Type | Default | Description |
|---|---|---|---|
| `model` | `str \| None` | `None` | Default model ID; required unless passed per call |
| `temperature` | `float \| None` | `None` | Sampling temperature [0, 2] |
| `top_p` | `float \| None` | `None` | Nucleus sampling probability (0, 1] |
| `presence_penalty` | `float \| None` | `None` | Presence penalty [-2.0, 2.0] |
| `frequency_penalty` | `float \| None` | `None` | Frequency penalty [-2.0, 2.0] |
| `max_tokens` | `int \| None` | `None` | Maximum tokens to generate |
| `stop` | `list[str] \| None` | `None` | Up to 4 stop sequences |

Configuration values are **defaults** — every call-time parameter overrides the matching field.

---

### Per-call Parameter Overrides

All chat methods accept per-call overrides that take priority over `configuration`:

```python
response = await llm.achat(
    messages=[...],
    model="gpt-4o-mini",      # Overrides configuration.model
    temperature=0.0,           # Overrides configuration.temperature
    top_p=None,
    presence_penalty=None,
    frequency_penalty=None,
    max_tokens=1024,
    stop=["DONE"],
    extra_body={"key": "val"}, # Extra JSON payload forwarded to the provider
)
```

---

### Custom Endpoint (Azure OpenAI / proxies)

`api_base` on `OpenAILlm` lets you point to any OpenAI-compatible endpoint:

```python
# Azure OpenAI
llm = OpenAILlm(
    api_key="your-azure-key",
    api_base="https://<resource>.openai.azure.com/openai/deployments/<deployment>",
    configuration=OpenAIConfiguration(model="gpt-4o"),
)

# Local proxy / gateway
llm = OpenAILlm(
    api_key="sk-xxx",
    api_base="http://localhost:4000/v1",
    configuration=OpenAIConfiguration(model="gpt-4o"),
)
```

## LLM Methods

### achat / chat — Chat Completion

```python
response: Response = await llm.achat(
    messages=[
        Message.from_text("You are a helpful assistant.", role=Role.SYSTEM),
        Message.from_text("What is Python?", role=Role.USER),
    ],
    model=None,              # Optional override
    temperature=None,        # Optional override
    max_tokens=None,         # Optional override
    tools=None,              # Optional List[Tool]
)
answer = response.message.content  # str
```

### astream — Streaming

```python
from bridgic.core.model.types import AsyncStreamResponse

stream: AsyncStreamResponse = await llm.astream(
    messages=[Message.from_text("Tell me a story", role=Role.USER)]
)
async for chunk in stream:
    print(chunk.delta)  # MessageChunk.delta: Optional[str]
```

### aselect_tool — Tool Selection

```python
from bridgic.core.model.types import ToolCall

tool_calls, text = await llm.aselect_tool(
    messages=[Message.from_text("What's the weather?", role=Role.USER)],
    tools=[weather_tool],
)
# tool_calls: List[ToolCall]
# text: Optional[str] — optional response text alongside tool calls
```

### astructured_output — Structured Output

When you need the LLM to return structured data, **always prefer `astructured_output` over manual JSON parsing**. It guarantees valid output matching your schema.

```python
from pydantic import BaseModel, Field
from bridgic.core.model.protocols import PydanticModel

class Plan(BaseModel):
    steps: list[str]
    priority: str = Field(description="high, medium, or low")

result: Plan = await llm.astructured_output(
    messages=[
        Message.from_text("You are a task planner.", role=Role.SYSTEM),
        Message.from_text("Plan: build a website", role=Role.USER),
    ],
    constraint=PydanticModel(model=Plan),
)
# result is a Plan instance — fully typed, no JSON parsing needed
```

**Constraint types** (`from bridgic.core.model.protocols import ...`):
- `PydanticModel(model=MyModel)` — returns a Pydantic model instance (recommended)
- `JsonSchema(name="plan", schema_dict={...})` — returns a dict matching JSON Schema

## LLM Worker Pattern

Using LLM inside a Bridgic worker:

```python
from bridgic.asl import ASLAutoma, graph
from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration
from bridgic.core.model.types import Message, Role

async def llm_worker(prompt: str, llm: OpenAILlm) -> str:
    response = await llm.achat(messages=[
        Message.from_text(prompt, role=Role.USER)
    ])
    return response.message.content

class LLMAgent(ASLAutoma):
    def __init__(self, llm: OpenAILlm):
        self.llm = llm
        super().__init__()

    with graph as g:
        prepare = format_prompt
        generate = llm_worker
        parse = parse_response

        +prepare >> generate >> ~parse
```

## Multi-LLM Pattern

Use different LLMs for different tasks:

```python
from bridgic.asl import ASLAutoma, graph
from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration

class MultiLLMAgent(ASLAutoma):
    def __init__(self):
        self.fast_llm = OpenAILlm(
            api_key="...",
            configuration=OpenAIConfiguration(model="gpt-4o-mini"),
        )
        self.smart_llm = OpenAILlm(
            api_key="...",
            configuration=OpenAIConfiguration(model="gpt-4o"),
        )
        super().__init__()

    with graph as g:
        classify = classify_complexity   # Use fast LLM
        simple_response = generate_simple  # Use fast LLM
        complex_response = generate_complex  # Use smart LLM

        +classify
        # Router decides based on complexity via ferry_to()
```

## RAG Pattern

```python
from bridgic.asl import ASLAutoma, graph

class RAGAgent(ASLAutoma):
    with graph as g:
        embed_query = embed_query_fn
        retrieve = vector_search
        rerank = rerank_results
        generate = llm_generate

        +embed_query >> retrieve >> rerank >> ~generate
```
