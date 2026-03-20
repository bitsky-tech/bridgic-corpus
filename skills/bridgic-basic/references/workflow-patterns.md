# Workflow Patterns

Common patterns for building workflows with Bridgic. All examples use ASL syntax.

## Pipeline Patterns

### Linear Pipeline

```python
from bridgic.asl import ASLAutoma, graph

class DataPipeline(ASLAutoma):
    with graph as g:
        validate = validate_input
        transform = transform_data
        enrich = enrich_data
        store = store_results

        +validate >> transform >> enrich >> ~store
```

### Pipeline with Error Handling

Use `ferry_to()` to branch to an error handler:

```python
from bridgic.asl import ASLAutoma, graph
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System

async def validate_with_fallback(
    input: dict,
    automa: GraphAutoma = System("automa")
) -> dict:
    try:
        validated = validate(input)
        automa.ferry_to("process", data=validated)
    except ValidationError as e:
        automa.ferry_to("handle_error", error=str(e))
    return input

class RobustPipeline(ASLAutoma):
    with graph as g:
        validate = validate_with_fallback
        process = process_data
        handle_error = error_handler
        finalize = final_step

        +validate
        process >> finalize
        handle_error >> finalize
        ~finalize
```

## Fan-Out / Fan-In Patterns

### Basic Fan-Out

One worker triggers multiple parallel workers:

```python
from bridgic.asl import ASLAutoma, graph

class FanOutAgent(ASLAutoma):
    with graph as g:
        source = generate_tasks
        task_a = process_type_a
        task_b = process_type_b
        task_c = process_type_c

        +source >> (task_a & task_b & task_c)
        ~task_a, ~task_b, ~task_c
```

### Fan-In with Merge

Multiple workers feed into one. **Use `ArgsMappingRule.MERGE`** — receiver gets a **list**, not dict.

```python
from bridgic.asl import ASLAutoma, graph, Settings
from bridgic.core.automa.args import ArgsMappingRule

async def merge_results(results: list) -> dict:
    # results = [result_web, result_db, result_cache] — a list!
    combined = {}
    for r in results:
        combined.update(r)
    return combined

class FanInAgent(ASLAutoma):
    with graph as g:
        query = parse_query
        search_web = web_search
        search_db = db_search
        search_cache = cache_search
        merge = merge_results * Settings(args_mapping_rule=ArgsMappingRule.MERGE)

        +query >> (search_web & search_db & search_cache) >> ~merge
```

### Diamond Pattern

Fan-out then fan-in:

```python
from bridgic.asl import ASLAutoma, graph, Settings
from bridgic.core.automa.args import ArgsMappingRule

class DiamondAgent(ASLAutoma):
    with graph as g:
        split = split_work
        path_a = process_a
        path_b = process_b
        join = combine_results * Settings(args_mapping_rule=ArgsMappingRule.MERGE)

        +split >> (path_a & path_b) >> ~join
```

## Routing Patterns

### Conditional Router

Route based on input using `ferry_to()`:

```python
from bridgic.asl import ASLAutoma, graph
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System

async def router(
    input: dict,
    automa: GraphAutoma = System("automa")
) -> dict:
    input_type = input.get("type")
    if input_type == "text":
        automa.ferry_to("text_handler", data=input)
    elif input_type == "image":
        automa.ferry_to("image_handler", data=input)
    else:
        automa.ferry_to("default_handler", data=input)
    return input

class RouterAgent(ASLAutoma):
    with graph as g:
        route = router
        text_handler = handle_text
        image_handler = handle_image
        default_handler = handle_default
        output = format_output

        +route
        text_handler >> output
        image_handler >> output
        default_handler >> output
        ~output
```

### Priority Router

```python
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System

async def priority_router(
    task: dict,
    automa: GraphAutoma = System("automa")
) -> dict:
    priority = task.get("priority", "normal")
    handlers = {
        "critical": "critical_handler",
        "high": "high_priority_handler",
        "normal": "normal_handler",
        "low": "batch_handler"
    }
    automa.ferry_to(handlers.get(priority, "normal_handler"), task=task)
    return task
```

### Dynamic Router with Independent Outputs

Each handler is an output, only one runs per request:

```python
from bridgic.asl import ASLAutoma, graph

class RequestRouterAgent(ASLAutoma):
    with graph as g:
        router = classify_and_route
        fast_handler = handle_fast
        text_handler = handle_text
        image_handler = handle_image

        +router, ~fast_handler, ~text_handler, ~image_handler
```

## Loop Patterns

### Iterative Processing with Local Space

```python
from bridgic.asl import ASLAutoma, graph
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System, RuntimeContext

async def iterator(
    items: list,
    index: int = 0,
    automa: GraphAutoma = System("automa"),
    ctx: RuntimeContext = System("runtime_context")
) -> list:
    local_space = automa.get_local_space(ctx)

    if index < len(items):
        result = await process_item(items[index])
        results = local_space.get("results", [])
        results.append(result)
        local_space["results"] = results
        automa.ferry_to("loop", items=items, index=index + 1)

    return local_space.get("results", [])

class IteratorAgent(ASLAutoma):
    with graph as g:
        loop = iterator
        +loop >> ~loop
```

### Retry Pattern

```python
import asyncio
from bridgic.asl import ASLAutoma, graph
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System

async def retry_worker(
    task: dict,
    retry_count: int = 0,
    max_retries: int = 3,
    automa: GraphAutoma = System("automa")
) -> dict:
    try:
        result = await risky_operation(task)
        automa.ferry_to("success", result=result)
    except Exception as e:
        if retry_count < max_retries:
            await asyncio.sleep(2 ** retry_count)
            automa.ferry_to("retry", task=task, retry_count=retry_count + 1)
        else:
            automa.ferry_to("failure", error=str(e))
    return task

class RetryAgent(ASLAutoma):
    with graph as g:
        retry = retry_worker
        success = handle_success
        failure = handle_failure

        +retry
        ~success, ~failure
```

## Aggregation Patterns

### Dynamic Parallel Collection

```python
from bridgic.asl import ASLAutoma, graph, concurrent, ASLField, Settings, Data
from bridgic.core.automa.args import ResultDispatchingRule, ArgsMappingRule

class CollectorAgent(ASLAutoma):
    with graph as g:
        prepare = fetch_items

        with concurrent(items=ASLField(list, dispatching_rule=ResultDispatchingRule.IN_ORDER)):
            collectors = lambda items: (
                fetch_item * Settings(key=f"fetch_{i}") * Data(item=item)
                for i, item in enumerate(items)
            )

        aggregate = aggregate_all * Settings(args_mapping_rule=ArgsMappingRule.MERGE)

        +prepare >> concurrent >> ~aggregate
```

## State Management Patterns

### Checkpoint Pattern

```python
from bridgic.asl import ASLAutoma, graph
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System, RuntimeContext
from datetime import datetime

async def checkpoint_worker(
    data: dict,
    automa: GraphAutoma = System("automa"),
    ctx: RuntimeContext = System("runtime_context")
) -> dict:
    local_space = automa.get_local_space(ctx)
    checkpoint = {
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "step": local_space.get("current_step", 0)
    }
    local_space["checkpoint"] = checkpoint
    return data
```
