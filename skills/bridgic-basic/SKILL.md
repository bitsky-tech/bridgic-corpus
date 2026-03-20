---
name: bridgic-basic
description: "This skill should be used when the user asks to \"create an agent with Bridgic\", \"build a workflow\", \"define workers\", \"use ASL syntax\", \"create GraphAutoma\", \"add dynamic routing\", \"use ferry_to\", \"implement ReCENT memory\", \"compose automas\", \"configure worker dependencies\", \"use From or System injection\", \"add worker callbacks\", \"implement human-in-the-loop\", \"use ConcurrentAutoma\", \"use SequentialAutoma\", \"integrate MCP server\", \"use MCP tools\", \"add tracing\", \"use Opik\", \"debug Bridgic agent\", \"enable verbose mode\", \"persist local space\", \"handle events\", \"post_event\", \"request_feedback\", \"create Automa tool\", \"use @as_tool\", or needs guidance on Bridgic framework concepts, parameter passing (ArgsMappingRule, ResultDispatchingRule), dynamic topology, MCP integration, observability, event handling, debugging, or agentic system development."
---

# Bridgic Agent Development

Bridgic is an agentic programming framework built around Dynamic Topology Orchestration, Component-Oriented Paradigm, and ASL (Agent Structure Language).

## Core Concepts

### Worker and Automa

- **Worker**: Basic execution unit (function, method, or class with `arun`/`run` methods)
- **Automa**: Orchestrator managing workers in a Dynamic Directed Graph (DDG)
- **Key insight**: Automa inherits from Worker, enabling hierarchical nesting

### API Hierarchy

1. **Core API**: Direct `GraphAutoma` with `@worker` decorator
2. **ASL (Recommended)**: Declarative DSL with `with graph as g:` syntax

### Automa Types

| Type | Use Case |
|------|----------|
| `GraphAutoma` / `ASLAutoma` | Complex workflows with dependencies, branching, dynamic topology |
| `ConcurrentAutoma` | Simple parallel execution of independent workers |
| `SequentialAutoma` | Simple sequential pipeline without complex dependencies |
| `ReCentAutoma` | Autonomous agents with LLM, tools, and memory management |

## Essential Imports

```python
# Core
from bridgic.core.automa import GraphAutoma, worker, RunningOptions

# ASL (recommended)
from bridgic.asl import ASLAutoma, graph, concurrent, Settings, Data, ASLField

# Parameter Passing
from bridgic.core.automa.args import (
    From,                    # Inject from other worker's output
    System,                  # Inject system resources (automa, runtime_context)
    ArgsMappingRule,         # AS_IS, MERGE, UNPACK, SUPPRESSED
    ResultDispatchingRule,   # AS_IS, IN_ORDER
    RuntimeContext,          # Data persistence
    InOrder,                 # Distribute data to multiple workers
)

# Callbacks
from bridgic.core.automa.worker import WorkerCallback, WorkerCallbackBuilder

# Human Interaction & Event Handling
from bridgic.core.automa.interaction import (
    Interaction, InteractionFeedback, InteractionException,  # Human-in-the-loop
    Event, Feedback, FeedbackSender,                         # Event handling
)

# Agentic
from bridgic.core.agentic import ConcurrentAutoma, SequentialAutoma
from bridgic.core.agentic.recent import ReCentAutoma, StopCondition, ReCentMemoryConfig
from bridgic.core.agentic.tool_specs import FunctionToolSpec, AutomaToolSpec, ToolSetBuilder, as_tool

# MCP Integration
from bridgic.protocols.mcp import McpServerConnectionStdio, McpToolSetBuilder

# LLM Integration
from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration
from bridgic.core.model.types import Message, Role, Response
```

## LLM Types and Usage

### Message Construction

`Message` does NOT accept `content` as a constructor parameter. Use factory methods:

```python
from bridgic.core.model.types import Message, Role

# CORRECT: Use factory methods
msg = Message.from_text("Hello", role=Role.USER)
system_msg = Message.from_text("You are a helpful assistant.", role=Role.SYSTEM)

# WRONG: content is NOT a constructor parameter
# msg = Message(role=Role.USER, content="Hello")  # This will FAIL!
```

### Message Properties

- `message.content` — property that joins all TextBlock texts with `"\n\n"`
- `message.blocks` — raw list of ContentBlock (TextBlock, ToolCallBlock, ToolResultBlock)
- `message.role` — Role enum value

### Role Enum

```python
class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    AI = "assistant"   # NOTE: string value is "assistant", not "ai"
    TOOL = "tool"
```

### Response Object

`achat()` / `chat()` returns a `Response`, NOT a Message directly:

```python
from bridgic.core.model.types import Response

response: Response = await llm.achat(messages=[...])
# Response fields:
#   response.message: Optional[Message]  — the structured message
#   response.raw: Optional[Any]          — raw provider response

# CORRECT: Access text content via message.content
text = response.message.content

# WRONG: Response has no .content attribute
# text = response.content  # AttributeError!
```

### LLM Methods

```python
llm = OpenAILlm(api_key="...", configuration=OpenAIConfiguration(model="gpt-4o"))

# Chat (sync/async) → returns Response
response: Response = await llm.achat(messages=[...])
response: Response = llm.chat(messages=[...])

# Streaming (sync/async) → yields MessageChunk
async for chunk in llm.astream(messages=[...]):
    print(chunk.delta)  # MessageChunk.delta: Optional[str]

# Tool selection → returns (List[ToolCall], Optional[str])
tool_calls, text = await llm.aselect_tool(messages=[...], tools=[...])
```

### Structured Output (Recommended for JSON)

When you need the LLM to return structured data (JSON, lists, etc.), **always prefer `astructured_output` over manual JSON parsing from `achat`**. It guarantees valid output matching your schema.

```python
from pydantic import BaseModel, Field
from bridgic.core.model.protocols import PydanticModel

# 1. Define your schema as a Pydantic model
class Plan(BaseModel):
    steps: list[Step]

class Step(BaseModel):
    id: int
    title: str = Field(description="Short title of the step")
    description: str = Field(description="Detailed description")
    depends_on: list[int] = Field(default=[], description="IDs of steps this depends on")

# 2. Call astructured_output with PydanticModel constraint
result: Plan = await llm.astructured_output(
    messages=[
        Message.from_text("You are a task planner.", role=Role.SYSTEM),
        Message.from_text("Break down: build a website", role=Role.USER),
    ],
    constraint=PydanticModel(model=Plan),  # Wraps Pydantic class
)

# result is a Plan instance — fully typed, no JSON parsing needed
for step in result.steps:
    print(f"[{step.id}] {step.title}")
```

**Constraint types** (`from bridgic.core.model.protocols import ...`):
- `PydanticModel(model=MyModel)` — returns a Pydantic model instance (recommended)
- `JsonSchema(name="plan", schema_dict={...})` — returns a dict matching JSON Schema
- `Regex(pattern=r"...")` — output matches regex pattern
- `Choice(choices=["A", "B", "C"])` — output is one of the choices

### Complete LLM Call Example

```python
from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration
from bridgic.core.model.types import Message, Role

llm = OpenAILlm(
    api_key=api_key,
    timeout=30,
    configuration=OpenAIConfiguration(model="gpt-4o", temperature=0.7),
)

response = await llm.achat(
    messages=[
        Message.from_text("You are a helpful assistant.", role=Role.SYSTEM),
        Message.from_text("What is Python?", role=Role.USER),
    ]
)

answer = response.message.content  # str
```

## ASL Quick Reference

### Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `+` | Mark as start worker (unary) | `+a` |
| `~` | Mark as output worker (unary) | `~b` |
| `>>` | Add dependency (a runs before b) | `a >> b` |
| `&` | Group for parallel execution | `a & b` |
| `*` | Apply Settings or Data | `a * Settings(key="x")` |

### Basic Pattern

```python
from bridgic.asl import ASLAutoma, graph

class MyAgent(ASLAutoma):
    with graph as g:
        a = worker_func_a
        b = worker_func_b
        +a >> ~b  # a is start, b is output, a runs before b
```

## Parameter Passing System

### ArgsMappingRule (Receiver Rules)

Controls how a worker receives results from its dependencies:

| Rule | Behavior |
|------|----------|
| `AS_IS` (default) | Pass each dependency result as positional arg in dependency order |
| `MERGE` | Wrap all dependency results in a **list** as single argument |
| `UNPACK` | Unpack single dependency result (list/tuple → args, dict → kwargs) |
| `SUPPRESSED` | Ignore all dependency results |

**MERGE Example** (receives list, not dict):
```python
async def merge_handler(results: list) -> Any:
    # results = [result_from_dep1, result_from_dep2, ...]
    return sum(results)

class Agent(ASLAutoma):
    with graph as g:
        a = task_a
        b = task_b
        merge = merge_handler * Settings(args_mapping_rule=ArgsMappingRule.MERGE)
        +(a & b) >> ~merge
```

### ResultDispatchingRule (Sender Rules)

Controls how a worker dispatches its result to downstream workers:

| Rule | Behavior |
|------|----------|
| `AS_IS` (default) | Send entire result to all downstream workers |
| `IN_ORDER` | Distribute list elements to downstream workers in order |

### Arguments Injection

**From()** - Inject output from any worker (not just dependencies):
```python
async def worker_c(
    primary: str,
    from_a: str = From("worker_a"),           # Required injection
    from_b: str = From("worker_b", default="") # Optional with default
) -> str:
    return f"{primary} {from_a} {from_b}"
```

**System()** - Inject system resources:
```python
async def dynamic_worker(
    input: str,
    automa: GraphAutoma = System("automa"),           # Current automa
    ctx: RuntimeContext = System("runtime_context"),   # Worker context (has worker_key)
    sub: GraphAutoma = System("automa:sub_worker")    # Sub-automa by key
) -> str:
    # Use automa.ferry_to(), automa.add_worker(), etc.
    # Use local_space for data persistence
    local_space = automa.get_local_space(ctx)
    local_space["key"] = "value"  # Persist data
    return input
```

## Dynamic Routing with ferry_to()

Jump to any worker at runtime, bypassing normal dependency flow:

```python
async def router(
    input: str,
    automa: GraphAutoma = System("automa")
) -> str:
    if "urgent" in input:
        automa.ferry_to("fast_handler", input)        # positional arg
    else:
        automa.ferry_to("normal_handler", text=input) # keyword arg
    return input

class RouterAgent(ASLAutoma):
    with graph as g:
        route = router
        fast_handler = handle_fast      # receives: def handle_fast(text: str)
        normal_handler = handle_normal  # receives: def handle_normal(text: str)
        +route, ~fast_handler, ~normal_handler
```

**Signature:** `ferry_to(key, *args, **kwargs)` - args/kwargs are passed directly to the target worker.

## Dynamic Topology

Add/remove workers at runtime:

```python
async def dynamic_builder(
    tasks: list,
    automa: GraphAutoma = System("automa")
) -> int:
    # Add task workers dynamically
    for i, task in enumerate(tasks):
        automa.add_func_as_worker(
            key=f"task_{i}",
            func=process_task,
            dependencies=["dynamic_builder"]
        )
    # Add single collector as output (only one output allowed)
    automa.add_func_as_worker(
        key="collect",
        func=collect_results,
        dependencies=[f"task_{i}" for i in range(len(tasks))],
        is_output=True
    )
    return len(tasks)
```

**Methods:**
- `add_func_as_worker(key, func, *, dependencies=[], is_start=False, is_output=False, args_mapping_rule=ArgsMappingRule.AS_IS, result_dispatching_rule=ResultDispatchingRule.AS_IS, callback_builders=[])`
- `add_worker(key, worker, *, dependencies=[], is_start=False, is_output=False, ...)`
- `remove_worker(key)`
- `add_dependency(key, dependency)`

**Note:** All parameters after `func`/`worker` are keyword-only. Only one worker can have `is_output=True`. Use a collector to gather multiple results.

## Worker Callbacks

Non-intrusive monitoring and error handling:

```python
class MyCallback(WorkerCallback):
    async def on_worker_start(self, key, is_top_level, parent, arguments):
        print(f"Starting {key}")

    async def on_worker_end(self, key, is_top_level, parent, arguments, result):
        print(f"Completed {key}: {result}")

    async def on_worker_error(self, key, is_top_level, parent, arguments, error: ValueError) -> bool:
        # Type annotation determines which exceptions to handle
        print(f"Error in {key}: {error}")
        return True  # Return True to suppress exception

# Register callback
result = await automa.arun(
    input="data",
    options=RunningOptions(callback_builders=[WorkerCallbackBuilder(MyCallback)])
)

# With dependency injection
result = await automa.arun(
    input="data",
    options=RunningOptions(callback_builders=[
        WorkerCallbackBuilder(MyCallback, init_kwargs={"logger": my_logger})
    ])
)
```

## Event Handling

Real-time communication between workers and the application layer without interrupting execution:

```python
import asyncio
from bridgic.core.automa.interaction import Event, Feedback, FeedbackSender

# Register event handler on the automa
def handle_progress(event: Event):
    print(f"Progress: {event.data}")

automa.register_event_handler("progress", handle_progress)

# Worker can post events during execution
async def long_task(automa: GraphAutoma = System("automa")) -> str:
    for i in range(10):
        automa.post_event(Event(event_type="progress", data=i/10))
        await asyncio.sleep(0.1)
    return "done"
```

**With feedback** (worker waits for response):
```python
def handle_with_feedback(event: Event, sender: FeedbackSender):
    # Process event and send feedback
    sender.send(Feedback(data="approved"))

automa.register_event_handler("approval", handle_with_feedback)

# Worker requests feedback
async def approval_worker(automa: GraphAutoma = System("automa")) -> str:
    feedback = await automa.request_feedback_async(
        Event(event_type="approval", data="Need approval"),
        timeout=30.0  # Optional timeout in seconds
    )
    return feedback.data
```

**Note:** Event handlers only work on top-level Automa. For long-running interactions that require process persistence, use Human-in-the-Loop instead.

## Human-in-the-Loop

Pause execution for human input with state serialization:

```python
from bridgic.core.automa.interaction import InteractionException, InteractionFeedback

try:
    result = await automa.arun(input="data")
except InteractionException as e:
    # e.interactions: List of pending interactions
    # e.snapshot: Serialized automa state
    snapshot = e.snapshot

    # ... collect human feedback asynchronously ...

    # Resume execution (load_from_snapshot is a classmethod)
    restored_automa = MyAutomaClass.load_from_snapshot(snapshot)
    result = await restored_automa.arun(feedback_data=[
        InteractionFeedback(interaction_id="...", data="user input")
    ])
```

## Automa Execution

### arun() Signature

```python
result = await automa.arun(
    *args,                    # Positional args passed to start workers
    **kwargs,                 # Keyword args passed to start workers
)

# With RunningOptions (passed as keyword 'options')
result = await automa.arun(
    input="data",
    options=RunningOptions(debug=True, verbose=True, callback_builders=[...]),
)

# With feedback for human-in-the-loop resume
result = await automa.arun(
    feedback_data=[InteractionFeedback(interaction_id="...", data="user input")]
)
```

**Note:** `options` and `feedback_data` are special keyword args consumed by `arun()` itself; all other args/kwargs are forwarded to start workers.

## ReCENT Autonomous Agents

ReAct with memory compression to prevent context explosion:

```python
from bridgic.core.agentic.recent import ReCentAutoma, StopCondition
from bridgic.core.agentic.tool_specs import FunctionToolSpec

agent = ReCentAutoma(
    llm=llm,
    tools=[FunctionToolSpec(search), FunctionToolSpec(calculate)],
    stop_condition=StopCondition(
        max_iteration=15,
        max_consecutive_no_tool_selected=3
    )
)
result = await agent.arun(
    goal="Research and summarize topic X",
    guidance="Focus on recent developments from 2024"  # Optional guidance
)
```

## Creating Automa Tools with @as_tool

Convert an Automa workflow into a tool for use with ReCentAutoma:

```python
from bridgic.core.agentic.tool_specs import as_tool, AutomaToolSpec

# Define the tool spec function (provides name, description, and parameters)
def multiply(x: float, y: float):
    """Multiply two numbers together."""
    ...  # Implementation not needed - just for spec

# Decorate Automa class with @as_tool
@as_tool(multiply)
class MultiplyAutoma(GraphAutoma):
    @worker(is_start=True, is_output=True)
    async def multiply(self, x: float, y: float) -> float:
        return x * y

# Use as tool in ReCentAutoma
agent = ReCentAutoma(
    llm=llm,
    tools=[AutomaToolSpec(MultiplyAutoma)]
)
```

## Simple Parallel/Sequential Execution

For simpler use cases without complex dependencies:

```python
from bridgic.core.agentic import ConcurrentAutoma, SequentialAutoma

# Parallel execution - all workers run concurrently
concurrent = ConcurrentAutoma()
concurrent.add_func_as_worker("task_a", process_a)
concurrent.add_func_as_worker("task_b", process_b)
results = await concurrent.arun(input_data)  # Returns list of results

# Sequential execution - workers run in order added
sequential = SequentialAutoma()
sequential.add_func_as_worker("step_1", step_one)
sequential.add_func_as_worker("step_2", step_two)
result = await sequential.arun(input_data)  # Returns final result
```

**Note:** ConcurrentAutoma/SequentialAutoma have restrictions - they don't support `dependencies`, `ferry_to()`, or `remove_worker()`. Use GraphAutoma/ASLAutoma for complex workflows.

## Debugging & Configuration

### Debug Mode

Enable debug mode for verbose runtime information:

```python
from bridgic.core.automa import RunningOptions

# Via constructor
agent = MyAgent(running_options=RunningOptions(debug=True, verbose=True))

# Or at runtime
agent.set_running_options(debug=True, verbose=True)
```

**Note:** Top-level Automa settings override nested Automa settings (Setting Penetration Mechanism).

### Persisting Local Space

By default, worker local space is cleared after `arun()` completes. Override to persist:

```python
class StatefulAgent(ASLAutoma):
    def should_reset_local_space(self) -> bool:
        return False  # Keep local space between runs
```

## MCP Integration

Connect to MCP (Model Context Protocol) servers for external tool integration:

```python
from bridgic.protocols.mcp import McpToolSetBuilder

# Use McpToolSetBuilder - creates connection internally
tools = McpToolSetBuilder.stdio(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/path"],
    tool_names=["read_file", "write_file"]  # Optional: filter tools
)

# Use with ReCentAutoma
agent = ReCentAutoma(llm=llm, tools=tools)
```

See `references/integrations.md` for complete MCP and observability patterns.

## Additional Resources

### Reference Files — Core Concepts

| File | Scope |
|------|-------|
| `references/worker.md` | Worker interface, @worker decorator, CallableWorker |
| `references/automa-lifecycle.md` | Automa, GraphAutoma, lifecycle, execution, DDG, state management |
| `references/dynamic-topology.md` | ferry_to(), add_worker, remove_worker, deferred tasks |
| `references/parameter-system.md` | ArgsMappingRule, ResultDispatchingRule, From(), System(), local space |
| `references/callbacks.md` | WorkerCallback, WorkerCallbackBuilder, exception matching |
| `references/event-handling.md` | Event, Feedback, FeedbackSender, post_event, request_feedback |
| `references/human-interaction.md` | InteractionException, Snapshot, resume flow |

### Reference Files — DSL & Patterns

| File | Scope |
|------|-------|
| `references/asl-syntax.md` | ASL operators, Settings, Data, ASLField, concurrent container, common mistakes |
| `references/workflow-patterns.md` | Pipeline, Fan-out/in, Diamond, Routing, Loop, Retry, Aggregation |
| `references/composition-patterns.md` | Nesting, Microservice, Multi-agent, Supervisor, Plugin |

### Reference Files — Integrations

| File | Scope |
|------|-------|
| `references/llm-integration.md` | Message, Response, LLM calls, structured output, streaming |
| `references/autonomous-agents.md` | ReCentAutoma, tools, @as_tool, ConcurrentAutoma, SequentialAutoma |
| `references/mcp-integration.md` | MCP connections, McpToolSetBuilder, filtering |
| `references/observability.md` | Opik, LangWatch, custom tracing callbacks |

### Example Files

- **`examples/simple_pipeline.py`** - Basic sequential workflow
- **`examples/parallel_agent.py`** - Fan-out/fan-in with MERGE
- **`examples/dynamic_router.py`** - Conditional routing with ferry_to
- **`examples/recent_agent.py`** - Autonomous agent with ReCENT
- **`examples/core_api_example.py`** - Core API with @worker decorator