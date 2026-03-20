# Worker Callbacks

Non-intrusive monitoring, logging, validation, and error handling for workers.

## WorkerCallback Interface

```python
from bridgic.core.automa.worker import WorkerCallback
from typing import Dict, Any, Optional

class MyCallback(WorkerCallback):
    async def on_worker_start(
        self,
        key: str,                              # Worker identifier
        is_top_level: bool = False,            # True if top-level automa
        parent: Optional["Automa"] = None,     # Parent automa instance
        arguments: Dict[str, Any] = None,      # {"args": tuple, "kwargs": dict}
    ) -> None:
        print(f"Starting {key}")

    async def on_worker_end(
        self,
        key: str,
        is_top_level: bool = False,
        parent: Optional["Automa"] = None,
        arguments: Dict[str, Any] = None,
        result: Any = None,                    # Worker execution result
    ) -> None:
        print(f"Completed {key}: {result}")

    async def on_worker_error(
        self,
        key: str,
        is_top_level: bool = False,
        parent: Optional["Automa"] = None,
        arguments: Dict[str, Any] = None,
        error: Exception = None,               # Type annotation determines handled exceptions!
    ) -> bool:
        """
        Return True to suppress the exception.
        Return False to let the exception propagate.
        Note: InteractionException cannot be suppressed.
        """
        print(f"Error in {key}: {error}")
        return True  # Suppress Exception and subclasses
```

## Exception Matching

The **type annotation** on the `error` parameter determines which exceptions the callback handles:

| Annotation | Handles |
|------------|---------|
| `error: ValueError` | ValueError and subclasses |
| `error: Exception` | All exceptions |
| `error: TypeError` | TypeError and subclasses |

**Important:** `InteractionException` can **never** be suppressed — the framework enforces re-raise.

## Registering Callbacks

### Per-Worker (via @worker decorator)

```python
from bridgic.core.automa import GraphAutoma, worker
from bridgic.core.automa.worker import WorkerCallbackBuilder

@worker(callback_builders=[WorkerCallbackBuilder(MyCallback)])
async def monitored_worker(input: str) -> str:
    return input
```

### Per-Automa (via RunningOptions)

```python
from bridgic.core.automa import RunningOptions
from bridgic.core.automa.worker import WorkerCallbackBuilder

result = await automa.arun(
    input="data",
    options=RunningOptions(
        callback_builders=[WorkerCallbackBuilder(MyCallback)]
    )
)
```

### With Dependency Injection

```python
from bridgic.core.automa.worker import WorkerCallbackBuilder

WorkerCallbackBuilder(
    MyCallback,
    init_kwargs={"logger": my_logger, "metrics": my_metrics}
)
```

## Shared vs Independent Callbacks

```python
# Shared instance (default) - all workers share same callback instance
WorkerCallbackBuilder(MyCallback, is_shared=True)

# Independent instances - each worker gets its own callback instance
WorkerCallbackBuilder(MyCallback, is_shared=False)
```

## Example: Logging Callback

```python
from bridgic.core.automa.worker import WorkerCallback
from typing import Dict, Any, Optional

class LoggingCallback(WorkerCallback):
    def __init__(self, logger):
        self.logger = logger

    async def on_worker_start(
        self,
        key: str,
        is_top_level: bool = False,
        parent: Optional["Automa"] = None,
        arguments: Dict[str, Any] = None,
    ) -> None:
        self.logger.info(f"Starting {key}", extra={"args": arguments})

    async def on_worker_end(
        self,
        key: str,
        is_top_level: bool = False,
        parent: Optional["Automa"] = None,
        arguments: Dict[str, Any] = None,
        result: Any = None,
    ) -> None:
        self.logger.info(f"Completed {key}", extra={"result": result})

    async def on_worker_error(
        self,
        key: str,
        is_top_level: bool = False,
        parent: Optional["Automa"] = None,
        arguments: Dict[str, Any] = None,
        error: Exception = None,
    ) -> bool:
        self.logger.error(f"Failed {key}", extra={"error": str(error)})
        return False  # Don't suppress, let it propagate
```

## Example: Metrics Callback

```python
import time
from bridgic.core.automa.worker import WorkerCallback
from typing import Dict, Any, Optional

class MetricsCallback(WorkerCallback):
    def __init__(self, metrics_client):
        self.metrics = metrics_client
        self.start_times: dict[str, float] = {}

    async def on_worker_start(
        self,
        key: str,
        is_top_level: bool = False,
        parent: Optional["Automa"] = None,
        arguments: Dict[str, Any] = None,
    ) -> None:
        self.start_times[key] = time.time()

    async def on_worker_end(
        self,
        key: str,
        is_top_level: bool = False,
        parent: Optional["Automa"] = None,
        arguments: Dict[str, Any] = None,
        result: Any = None,
    ) -> None:
        duration = time.time() - self.start_times[key]
        self.metrics.timing(f"worker.{key}.duration", duration)
        self.metrics.increment(f"worker.{key}.success")

    async def on_worker_error(
        self,
        key: str,
        is_top_level: bool = False,
        parent: Optional["Automa"] = None,
        arguments: Dict[str, Any] = None,
        error: Exception = None,
    ) -> bool:
        self.metrics.increment(f"worker.{key}.error")
        return False
```

## Combining Multiple Callbacks

```python
from bridgic.core.automa import RunningOptions
from bridgic.core.automa.worker import WorkerCallbackBuilder

result = await agent.arun(
    input="data",
    options=RunningOptions(
        callback_builders=[
            WorkerCallbackBuilder(LoggingCallback, init_kwargs={"logger": my_logger}),
            WorkerCallbackBuilder(MetricsCallback, init_kwargs={"metrics_client": my_metrics}),
        ]
    )
)
```
