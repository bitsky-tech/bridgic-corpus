# Observability and Tracing

Bridgic integrates with observability platforms for monitoring agent execution.

## Opik Integration

[Opik](https://www.comet.com/docs/opik/) provides tracing and evaluation for LLM applications.

### Installation

```bash
pip install bridgic-traces-opik
```

### Basic Usage

```python
from bridgic.traces.opik import OpikTraceCallback
from bridgic.core.automa import RunningOptions
from bridgic.core.automa.worker import WorkerCallbackBuilder

callback = WorkerCallbackBuilder(OpikTraceCallback)

result = await agent.arun(
    goal="Complete task",
    options=RunningOptions(callback_builders=[callback]),
)
```

### With ReCentAutoma

```python
from bridgic.traces.opik import OpikTraceCallback
from bridgic.core.agentic.recent import ReCentAutoma, StopCondition
from bridgic.core.automa import RunningOptions
from bridgic.core.automa.worker import WorkerCallbackBuilder

agent = ReCentAutoma(
    llm=llm,
    tools=tools,
    stop_condition=StopCondition(max_iteration=10),
    running_options=RunningOptions(
        callback_builders=[WorkerCallbackBuilder(OpikTraceCallback)]
    ),
)

result = await agent.arun(goal="Research topic X")
# Traces automatically sent to Opik
```

### Manual Trace Context

```python
from bridgic.traces.opik import start_opik_trace

with start_opik_trace(name="my-workflow"):
    result = await agent.arun(goal="Do something")
```

## LangWatch Integration

[LangWatch](https://langwatch.ai/) provides LLM observability and analytics.

### Installation

```bash
pip install bridgic-traces-langwatch
```

### Usage

```python
from bridgic.traces.langwatch import LangWatchTraceCallback
from bridgic.core.automa import RunningOptions
from bridgic.core.automa.worker import WorkerCallbackBuilder

result = await agent.arun(
    goal="Complete task",
    options=RunningOptions(
        callback_builders=[WorkerCallbackBuilder(LangWatchTraceCallback)]
    ),
)
```

## Custom Tracing Callback

Build custom callbacks for your observability stack:

```python
import time
from bridgic.core.automa.worker import WorkerCallback
from typing import Dict, Any, Optional

class CustomTracingCallback(WorkerCallback):
    def __init__(self, tracer):
        self.tracer = tracer
        self.spans: dict[str, dict] = {}

    async def on_worker_start(
        self,
        key: str,
        is_top_level: bool = False,
        parent: Optional["Automa"] = None,
        arguments: Dict[str, Any] = None,
    ) -> None:
        span = self.tracer.start_span(
            name=key,
            attributes={
                "is_top_level": is_top_level,
                "arguments": str(arguments),
            },
        )
        self.spans[key] = {"span": span, "start": time.time()}

    async def on_worker_end(
        self,
        key: str,
        is_top_level: bool = False,
        parent: Optional["Automa"] = None,
        arguments: Dict[str, Any] = None,
        result: Any = None,
    ) -> None:
        if key in self.spans:
            duration = time.time() - self.spans[key]["start"]
            self.spans[key]["span"].set_attribute("duration_ms", duration * 1000)
            self.spans[key]["span"].end()

    async def on_worker_error(
        self,
        key: str,
        is_top_level: bool = False,
        parent: Optional["Automa"] = None,
        arguments: Dict[str, Any] = None,
        error: Exception = None,
    ) -> bool:
        if key in self.spans:
            self.spans[key]["span"].record_exception(error)
            self.spans[key]["span"].end()
        return False  # Don't suppress error
```

## Combining Multiple Callbacks

Stack multiple callbacks for comprehensive observability:

```python
from bridgic.traces.opik import OpikTraceCallback
from bridgic.core.automa import RunningOptions
from bridgic.core.automa.worker import WorkerCallbackBuilder

result = await agent.arun(
    goal="Complete task",
    options=RunningOptions(
        callback_builders=[
            WorkerCallbackBuilder(OpikTraceCallback),
            WorkerCallbackBuilder(MetricsCallback, init_kwargs={"client": metrics}),
            WorkerCallbackBuilder(LoggingCallback, init_kwargs={"logger": logger}),
        ],
        debug=True,
        verbose=True,
    ),
)
```

## Production vs Development Configuration

```python
from bridgic.core.automa import RunningOptions
from bridgic.core.automa.worker import WorkerCallbackBuilder

# Production
production_options = RunningOptions(
    callback_builders=[
        WorkerCallbackBuilder(OpikTraceCallback),
        WorkerCallbackBuilder(MetricsCallback),
    ],
    debug=False,
    verbose=False,
)

# Development
dev_options = RunningOptions(
    callback_builders=[
        WorkerCallbackBuilder(LoggingCallback),
    ],
    debug=True,
    verbose=True,
)
```
