# Parameter Passing System

Bridgic's parameter system controls how data flows between workers via ArgsMappingRule (receiver) and ResultDispatchingRule (sender), plus From() and System() injection.

## ArgsMappingRule (Receiver Rules)

Controls how a worker receives results from its dependencies.

```python
from bridgic.core.automa.args import ArgsMappingRule
```

| Rule | Behavior |
|------|----------|
| `AS_IS` (default) | Pass each dependency result as positional arg in dependency order |
| `MERGE` | Wrap all dependency results in a **list** as single argument |
| `UNPACK` | Unpack single dependency result (list/tuple -> *args, dict -> **kwargs). Requires exactly one dependency. |
| `SUPPRESSED` | Ignore all dependency results, pass no arguments from dependencies |

### AS_IS Example

```python
async def a() -> str:
    return "hello"

async def b() -> str:
    return "world"

async def c(input_a: str, input_b: str) -> str:
    # Receives ("hello", "world") as positional args in dependency order
    return f"{input_a} {input_b}"
```

### MERGE Example

**Important:** MERGE wraps results in a **list**, NOT a dict.

```python
from bridgic.asl import ASLAutoma, graph, Settings
from bridgic.core.automa.args import ArgsMappingRule

async def merge_handler(results: list) -> dict:
    # results = [result_from_dep1, result_from_dep2, ...]
    combined = {}
    for r in results:
        combined.update(r)
    return combined

class Agent(ASLAutoma):
    with graph as g:
        a = task_a
        b = task_b
        merge = merge_handler * Settings(args_mapping_rule=ArgsMappingRule.MERGE)
        +(a & b) >> ~merge
```

### UNPACK Example

```python
async def producer() -> dict:
    return {"a": 1, "b": 2}

async def consumer(a: int, b: int) -> int:
    return a + b

# With UNPACK, consumer receives a=1, b=2 as kwargs
```

### SUPPRESSED Example

```python
from bridgic.asl import ASLAutoma, graph, Settings
from bridgic.core.automa.args import ArgsMappingRule

async def independent_worker() -> str:
    return "independent"

class Agent(ASLAutoma):
    with graph as g:
        a = task_a
        b = independent_worker * Settings(args_mapping_rule=ArgsMappingRule.SUPPRESSED)
        +a >> ~b  # b runs after a but doesn't receive a's result
```

## ResultDispatchingRule (Sender Rules)

Controls how a worker dispatches its result to downstream workers.

```python
from bridgic.core.automa.args import ResultDispatchingRule
```

| Rule | Behavior |
|------|----------|
| `AS_IS` (default) | Send entire result to all downstream workers |
| `IN_ORDER` | Distribute list elements to downstream workers in order |

### IN_ORDER Example

Result must be a list/tuple with length matching the number of downstream workers:

```python
from bridgic.asl import ASLAutoma, graph, Settings
from bridgic.core.automa.args import ResultDispatchingRule

async def splitter() -> list:
    return ["data_1", "data_2", "data_3"]

class Agent(ASLAutoma):
    with graph as g:
        split = splitter * Settings(result_dispatching_rule=ResultDispatchingRule.IN_ORDER)
        proc_1 = processor_1
        proc_2 = processor_2
        proc_3 = processor_3

        +split >> (proc_1 & proc_2 & proc_3)
        ~proc_1, ~proc_2, ~proc_3
        # proc_1 receives "data_1", proc_2 receives "data_2", etc.
```

## From() — Cross-Worker Result Injection

Inject results from any worker (not just dependencies):

```python
from bridgic.core.automa.args import From

async def worker_c(
    primary: str,
    from_a: str = From("worker_a"),                     # Required injection
    from_b: str = From("worker_b", default="fallback")  # Optional with default
) -> str:
    return f"{primary} + {from_a} + {from_b}"
```

**Error Handling:** If the worker specified in `From()` doesn't exist and no default is provided, `WorkerArgsInjectionError` is raised.

### Graceful Degradation with From()

```python
async def resilient_worker(
    primary: str,
    optional: str = From("might_fail", default="backup_value")
) -> str:
    return f"{primary} with {optional}"
```

## System() — Framework Resource Injection

Access framework internals via `System()`:

```python
from bridgic.core.automa.args import System, RuntimeContext
from bridgic.core.automa import GraphAutoma

async def worker_with_system(
    input: str,
    automa: GraphAutoma = System("automa"),           # Current automa instance
    ctx: RuntimeContext = System("runtime_context"),   # RuntimeContext for this worker
    sub: GraphAutoma = System("automa:sub_worker")    # Sub-automa by worker key
) -> str:
    # automa: Access to ferry_to(), add_worker(), remove_worker(), etc.
    # ctx: Contains worker_key for local space access

    # Access local space for data persistence
    local_space = automa.get_local_space(ctx)
    local_space["counter"] = local_space.get("counter", 0) + 1

    return input
```

### Supported System Keys

| Key | Returns | Description |
|-----|---------|-------------|
| `"runtime_context"` | RuntimeContext | Worker execution context (has `worker_key`) |
| `"automa"` | GraphAutoma | Current automa instance |
| `"automa:<worker_key>"` | GraphAutoma | Sub-automa instance by worker key |

## Local Space — Worker Data Persistence

Workers can persist data across `ferry_to()` loops using local space:

```python
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System, RuntimeContext

async def counter(
    automa: GraphAutoma = System("automa"),
    ctx: RuntimeContext = System("runtime_context")
) -> int:
    local_space = automa.get_local_space(ctx)
    count = local_space.get("count", 0) + 1
    local_space["count"] = count

    if count < 10:
        automa.ferry_to("counter")

    return count
```

**Note:** By default, local space is reset after `arun()` completes. Override `should_reset_local_space()` to persist between runs.
