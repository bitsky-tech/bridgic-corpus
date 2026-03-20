# Autonomous Agents

ReCentAutoma for autonomous agents, tool specifications, and simple automa types (ConcurrentAutoma, SequentialAutoma).

## ReCentAutoma

ReAct with memory compression to prevent context explosion:

```python
from bridgic.core.agentic.recent import ReCentAutoma, StopCondition
from bridgic.core.agentic.tool_specs import FunctionToolSpec
from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration

llm = OpenAILlm(
    api_key="your-api-key",
    configuration=OpenAIConfiguration(model="gpt-4o"),
)

agent = ReCentAutoma(
    llm=llm,
    tools=[FunctionToolSpec(search), FunctionToolSpec(calculate)],
    stop_condition=StopCondition(
        max_iteration=15,
        max_consecutive_no_tool_selected=3,
    ),
)

result = await agent.arun(
    goal="Research and summarize topic X",
    guidance="Focus on recent developments",  # Optional guidance
)
```

### ReCentAutoma Constructor

```python
ReCentAutoma(
    llm=...,                          # BaseLlm — required
    tools=None,                       # Optional List[Union[Callable, Automa, ToolSpec]]
    tools_builders=None,              # Optional List[ToolSetBuilder] (e.g., McpToolSetBuilder)
    stop_condition=None,              # Optional StopCondition
    memory_config=None,               # Optional ReCentMemoryConfig
    observation_task_config=None,     # Optional ObservationTaskConfig
    tool_task_config=None,            # Optional ToolTaskConfig
    answer_task_config=None,          # Optional AnswerTaskConfig
    name=None,                        # Optional str
    thread_pool=None,                 # Optional ThreadPoolExecutor
    running_options=None,             # Optional RunningOptions
)
```

### StopCondition

```python
from bridgic.core.agentic.recent import StopCondition

StopCondition(
    max_iteration=-1,                 # Max iterations (-1 = unlimited)
    max_consecutive_no_tool_selected=3,  # Stop after N iterations with no tool use
)
```

## Tool Specifications

### FunctionToolSpec

Wrap a function as a tool:

```python
from bridgic.core.agentic.tool_specs import FunctionToolSpec

async def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

tool = FunctionToolSpec(search_web)
# Or with custom metadata:
tool = FunctionToolSpec.from_raw(
    func=search_web,
    tool_name="web_search",
    tool_description="Search the web",
)
```

### AutomaToolSpec

Wrap an Automa as a tool:

```python
from bridgic.core.agentic.tool_specs import AutomaToolSpec

tool = AutomaToolSpec(MyAutoma())
# Or with custom metadata:
tool = AutomaToolSpec.from_raw(
    automa_cls=MyAutoma,
    tool_name="my_tool",
    tool_description="Does something",
)
```

### @as_tool Decorator

Convert an Automa class into a tool with explicit spec:

```python
from bridgic.core.agentic.tool_specs import as_tool, AutomaToolSpec
from bridgic.core.automa import GraphAutoma, worker

# Spec function provides name, description, and parameter schema
def multiply(x: float, y: float):
    """Multiply two numbers together."""
    ...  # Implementation not needed — just for spec

@as_tool(multiply)
class MultiplyAutoma(GraphAutoma):
    @worker(is_start=True, is_output=True)
    async def multiply(self, x: float, y: float) -> float:
        return x * y

# Use as tool in ReCentAutoma
agent = ReCentAutoma(
    llm=llm,
    tools=[AutomaToolSpec(MultiplyAutoma)],
)
```

### ToolSetBuilder

For dynamically building tool sets (e.g., MCP tools):

```python
from bridgic.core.agentic.tool_specs import ToolSetBuilder, ToolSetResponse

# ToolSetBuilder.build() -> ToolSetResponse
# ToolSetResponse = {"tool_specs": List[ToolSpec], "extras": Dict[str, Any]}
```

## ConcurrentAutoma

Execute multiple workers in parallel (simple, no complex dependencies):

```python
from bridgic.core.agentic import ConcurrentAutoma

async def fetch_user(user_id: int) -> dict:
    return {"id": user_id, "name": f"User {user_id}"}

async def fetch_orders(user_id: int) -> list:
    return [{"order_id": 1}, {"order_id": 2}]

async def fetch_preferences(user_id: int) -> dict:
    return {"theme": "dark"}

automa = ConcurrentAutoma(name="user-data-fetcher")
automa.add_func_as_worker(key="user", func=fetch_user)
automa.add_func_as_worker(key="orders", func=fetch_orders)
automa.add_func_as_worker(key="preferences", func=fetch_preferences)

# Returns dict: {"user": {...}, "orders": [...], "preferences": {...}}
results = await automa.arun(user_id=123)
```

## SequentialAutoma

Execute workers in sequence (order added):

```python
from bridgic.core.agentic import SequentialAutoma

async def validate(data: dict) -> dict:
    return {"validated": True, **data}

async def transform(data: dict) -> dict:
    return {"transformed": True, **data}

async def save(data: dict) -> str:
    return "saved"

automa = SequentialAutoma(name="data-pipeline")
automa.add_func_as_worker(key="validate", func=validate)
automa.add_func_as_worker(key="transform", func=transform)
automa.add_func_as_worker(key="save", func=save)

# Returns final result: "saved"
result = await automa.arun(data={"name": "test"})
```

## When to Use Each Type

| Type | Best For |
|------|----------|
| `GraphAutoma` / `ASLAutoma` | Complex dependencies, conditional routing, dynamic topology |
| `ConcurrentAutoma` | Independent parallel tasks, aggregating multiple data sources |
| `SequentialAutoma` | Simple pipelines, ETL workflows, step-by-step processing |
| `ReCentAutoma` | Autonomous agents, goal-directed behavior, tool use |

**Note:** ConcurrentAutoma/SequentialAutoma don't support `dependencies`, `ferry_to()`, or `remove_worker()`. Use GraphAutoma/ASLAutoma for complex workflows.
