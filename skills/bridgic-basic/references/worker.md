# Worker

The Worker is the basic execution unit in Bridgic. It represents a single task or operation.

## Worker Interface

```python
class Worker:
    key: str  # Unique identifier within its automa

    async def arun(self, *args, **kwargs) -> Any:
        """Async execution"""
        ...

    def run(self, *args, **kwargs) -> Any:
        """Sync execution (wraps arun)"""
        ...

    def ferry_to(self, key: str, /, *args, **kwargs):
        """Handoff control flow to specified worker"""
        ...

    def interact_with_human(self, event: Event) -> InteractionFeedback:
        """Request human input, raises InteractionException"""
        ...
```

## Creating Workers

### As Functions

Both sync and async functions can be used as workers:

```python
async def process_data(input: str) -> str:
    return input.upper()

def sync_process(input: str) -> str:
    return input.lower()
```

### With @worker Decorator

Use `@worker` on methods inside a `GraphAutoma` subclass:

```python
from bridgic.core.automa import GraphAutoma, worker

class MyAutoma(GraphAutoma):
    @worker(is_start=True)
    async def step_one(self, input: str) -> str:
        return f"Processed: {input}"

    @worker(dependencies=["step_one"], is_output=True)
    async def step_two(self, data: str) -> str:
        return f"Final: {data}"
```

### With CallableWorker

Wraps functions as Worker instances programmatically:

```python
from bridgic.core.automa.worker import CallableWorker

w = CallableWorker(
    func=my_function,
    key="custom_key"
)
```

## @worker Decorator Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | str | method name | Custom key identifier |
| `dependencies` | List[str] | [] | Worker keys this depends on |
| `is_start` | bool | False | Mark as entry point |
| `is_output` | bool | False | Mark as output worker |
| `args_mapping_rule` | ArgsMappingRule | AS_IS | How to receive args from dependencies |
| `result_dispatching_rule` | ResultDispatchingRule | AS_IS | How to dispatch results |
| `callback_builders` | List[WorkerCallbackBuilder] | [] | Callbacks for this worker |

## Async vs Sync Workers

- **Async workers**: Run concurrently in the event loop
- **Sync workers**: Run in thread pool if available, otherwise wrapped in `asyncio.to_thread`
- **Mixed**: Bridgic handles both seamlessly

```python
from concurrent.futures import ThreadPoolExecutor

thread_pool = ThreadPoolExecutor(max_workers=4)
automa = MyAutoma(thread_pool=thread_pool)
```
