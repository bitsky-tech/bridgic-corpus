# Composition Patterns

Patterns for composing multiple automas and building multi-agent systems.

## Automa as Worker (Nesting)

Since Automa inherits from Worker, automas can be nested:

```python
from bridgic.asl import ASLAutoma, graph

class InnerAutoma(ASLAutoma):
    with graph as g:
        a = task_a
        b = task_b
        +a >> ~b

class OuterAutoma(ASLAutoma):
    with graph as g:
        start = prepare
        inner = InnerAutoma()  # Nested automa as worker
        finish = finalize

        +start >> inner >> ~finish
```

### Accessing Nested Automas

```python
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System

async def worker_using_nested(
    input: str,
    sub_automa: GraphAutoma = System("automa:inner")  # Access by worker key
) -> str:
    # Can interact with nested automa
    return input
```

### Benefits of Composition

1. **Reusability**: Build once, use everywhere
2. **Encapsulation**: Hide complexity within sub-automas
3. **Testing**: Test components in isolation
4. **Modularity**: Replace components easily

## Microservice-Style Composition

```python
from bridgic.asl import ASLAutoma, graph

class AuthService(ASLAutoma):
    with graph as g:
        validate_token = token_validator
        get_user = user_fetcher
        +validate_token >> ~get_user

class DataService(ASLAutoma):
    with graph as g:
        fetch = data_fetcher
        transform = data_transformer
        +fetch >> ~transform

class NotificationService(ASLAutoma):
    with graph as g:
        format_msg = message_formatter
        send = message_sender
        +format_msg >> ~send

# Composed application
class Application(ASLAutoma):
    with graph as g:
        auth = AuthService()
        data = DataService()
        notify = NotificationService()

        +auth >> data >> ~notify
```

## Multi-Agent Collaboration

```python
from bridgic.asl import ASLAutoma, graph

class ResearchAgent(ASLAutoma):
    with graph as g:
        search = web_search
        analyze = analyze_results
        +search >> ~analyze

class WritingAgent(ASLAutoma):
    with graph as g:
        outline = create_outline
        write = write_content
        +outline >> ~write

class ReviewAgent(ASLAutoma):
    with graph as g:
        check = check_quality
        improve = suggest_improvements
        +check >> ~improve

class CollaborativeAgent(ASLAutoma):
    with graph as g:
        research = ResearchAgent()
        write = WritingAgent()
        review = ReviewAgent()

        +research >> write >> ~review
```

## Supervisor Pattern

A supervisor dynamically creates and manages sub-workers:

```python
from bridgic.asl import ASLAutoma, graph
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System, RuntimeContext, ArgsMappingRule

async def supervisor(
    task: dict,
    automa: GraphAutoma = System("automa"),
    ctx: RuntimeContext = System("runtime_context")
) -> dict:
    local_space = automa.get_local_space(ctx)
    subtasks = break_down_task(task)

    # Dynamically add task workers (deferred)
    for i, subtask in enumerate(subtasks):
        automa.add_func_as_worker(
            key=f"worker_{i}",
            func=specialist_worker,
            dependencies=["supervise"],
        )

    # Add collector as output
    automa.add_func_as_worker(
        key="collect",
        func=collect_results,
        dependencies=[f"worker_{i}" for i in range(len(subtasks))],
        is_output=True,
        args_mapping_rule=ArgsMappingRule.MERGE,
    )

    local_space["total_tasks"] = len(subtasks)
    return task

class SupervisedAgent(ASLAutoma):
    with graph as g:
        supervise = supervisor
        +supervise
```

## Chain of Responsibility

```python
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System

async def handler_chain(
    request: dict,
    handlers: list,
    index: int = 0,
    automa: GraphAutoma = System("automa")
) -> dict:
    if index < len(handlers):
        handler = handlers[index]
        result = await handler(request)

        if result.get("handled"):
            return result
        else:
            automa.ferry_to("chain", request=request, index=index + 1)

    return {"error": "No handler could process request"}
```

## Plugin Pattern

```python
from bridgic.asl import ASLAutoma, graph

class PluggableAgent(ASLAutoma):
    def __init__(self, plugins: list[ASLAutoma]):
        self._plugins = plugins
        super().__init__()

    with graph as g:
        pre_process = prepare_input
        post_process = finalize_output

        +pre_process >> ~post_process

    def _setup_plugins(self):
        for i, plugin in enumerate(self._plugins):
            self.add_worker(
                key=f"plugin_{i}",
                worker=plugin,
                dependencies=["pre_process"],
            )
```
