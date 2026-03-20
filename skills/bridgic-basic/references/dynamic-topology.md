# Dynamic Topology

Bridgic's Dynamic Directed Graph (DDG) supports runtime topology changes. Workers can be added, removed, and re-routed during execution.

## ferry_to() — Dynamic Routing

Jump to any worker at runtime, bypassing normal dependency flow:

```python
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System

async def router(
    input: str,
    automa: GraphAutoma = System("automa")
) -> str:
    if "urgent" in input:
        automa.ferry_to("fast_handler", input)        # positional arg
    else:
        automa.ferry_to("normal_handler", text=input)  # keyword arg
    return input
```

**Signature:** `ferry_to(key: str, /, *args, **kwargs)`
- `key`: Target worker key
- `*args, **kwargs`: Passed directly to the target worker

**Behavior:**
- Schedules the target worker to run in the **next event loop iteration**
- Bypasses normal dependency flow entirely
- Target worker does NOT need to have dependencies on the calling worker
- Multiple `ferry_to()` calls are allowed (all targets will be scheduled)

### Routing Pattern in ASL

```python
from bridgic.asl import ASLAutoma, graph

class RouterAgent(ASLAutoma):
    with graph as g:
        route = router
        fast_handler = handle_fast
        normal_handler = handle_normal

        # router is start, handlers are independent outputs
        # ferry_to() dynamically activates one handler
        +route, ~fast_handler, ~normal_handler
```

## add_func_as_worker() — Add Functions as Workers

```python
automa.add_func_as_worker(
    key="worker_key",
    func=my_function,
    *,  # All following params are keyword-only!
    dependencies=[],
    is_start=False,
    is_output=False,
    args_mapping_rule=ArgsMappingRule.AS_IS,
    result_dispatching_rule=ResultDispatchingRule.AS_IS,
    callback_builders=[],
)
```

**Critical:** All parameters after `func` are **keyword-only** (enforced by `*` separator).

## add_worker() — Add Worker Instances

```python
automa.add_worker(
    key="worker_key",
    worker=my_worker_instance,
    *,  # Keyword-only
    dependencies=[],
    is_start=False,
    is_output=False,
    args_mapping_rule=ArgsMappingRule.AS_IS,
    result_dispatching_rule=ResultDispatchingRule.AS_IS,
    callback_builders=[],
)
```

## remove_worker() — Remove a Worker

```python
automa.remove_worker("worker_key")
```

## add_dependency() — Add Dependency Between Workers

```python
automa.add_dependency(
    key="downstream_worker",
    dependency="upstream_worker"
)
```

## Deferred Execution

When called **during the Running Phase** (inside a worker), topology changes are **deferred**:
- Changes are queued and applied **between Dynamic Steps**
- This prevents graph corruption during concurrent execution
- The deferred change takes effect before the next round of worker scheduling

## Complete Example: Dynamic Worker Creation

```python
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System, ArgsMappingRule

async def supervisor(
    tasks: list,
    automa: GraphAutoma = System("automa")
) -> int:
    # Dynamically add task workers (deferred)
    for i, task in enumerate(tasks):
        automa.add_func_as_worker(
            key=f"task_{i}",
            func=process_task,
            dependencies=["supervisor"],
        )

    # Add a single collector as output
    automa.add_func_as_worker(
        key="collect",
        func=collect_results,
        dependencies=[f"task_{i}" for i in range(len(tasks))],
        is_output=True,
        args_mapping_rule=ArgsMappingRule.MERGE,
    )
    return len(tasks)
```

**Note:** Only one worker can have `is_output=True` per automa. Use a collector worker with `ArgsMappingRule.MERGE` to gather multiple results.
