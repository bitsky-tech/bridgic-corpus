# Automa Lifecycle

An Automa is an orchestrator that manages a collection of workers and their execution order. **Key insight: Automa inherits from Worker**, enabling hierarchical nesting.

## GraphAutoma

The primary Automa implementation using a Dynamic Directed Graph (DDG) topology:

```python
from bridgic.core.automa import GraphAutoma, worker

class MyWorkflow(GraphAutoma):
    @worker(is_start=True)
    async def start(self, input: str) -> str:
        return input

    @worker(dependencies=["start"], is_output=True)
    async def end(self, data: str) -> str:
        return data
```

## Execution Lifecycle

1. **Initialization Phase**: Workers registered, graph built
2. **Running Phase**: `arun()` or `run()` called
3. **Dynamic Steps (DS)**: Identify executable workers, execute, collect results
4. **Deferred Tasks**: Process add_worker/remove_worker requests between DS
5. **Result Collection**: Output workers' results returned

### Dynamic Steps (DS) Detail

Each Dynamic Step:
1. Identify executable workers (all dependencies satisfied)
2. Execute workers in parallel where possible
3. Collect results, update graph state
4. Process deferred topology changes (add_worker, remove_worker, add_dependency)
5. Repeat until all workers complete

## Execution Methods

```python
automa = MyWorkflow()

# Async execution (recommended)
result = await automa.arun(input="data")

# Sync execution
result = automa.run(input="data")

# With options
from bridgic.core.automa import RunningOptions

result = await automa.arun(
    input="data",
    options=RunningOptions(debug=True, verbose=True)
)
```

## arun() Signature

```python
async def arun(
    self,
    *args,                    # Positional args passed to start workers
    feedback_data=None,       # InteractionFeedback or List[InteractionFeedback]
    **kwargs,                 # Keyword args passed to start workers
) -> Any
```

**Special kwargs consumed by arun():**
- `options=RunningOptions(...)` — framework configuration
- `feedback_data=[...]` — for human-in-the-loop resume

All other kwargs are forwarded to start workers.

## RunningOptions

```python
from bridgic.core.automa import RunningOptions

RunningOptions(
    debug=False,            # Enable debug logging
    verbose=False,          # Enable verbose output
    callback_builders=[],   # List[WorkerCallbackBuilder] - initialization only
)
```

**Note:** `callback_builders` can only be set at initialization, not changed at runtime.

## Dynamic Directed Graph (DDG)

Unlike static graphs, DDG supports runtime topology changes:
- Workers can be added/removed during execution (as deferred tasks)
- Routing can change based on conditions via `ferry_to()`
- Enables both predictable workflows and adaptive agents

## State Management

### Serialization (Snapshot)

Snapshots are created internally when `InteractionException` is raised during human-in-the-loop:

```python
from bridgic.core.automa import Snapshot

# Snapshots are accessed via InteractionException
# There is NO get_snapshot() method!
try:
    result = await automa.arun(input="data")
except InteractionException as e:
    snapshot: Snapshot = e.snapshot  # Access snapshot from exception

# Restore from snapshot (classmethod)
restored = MyAutoma.load_from_snapshot(snapshot)

# Dict-based serialization
state_dict = automa.dump_to_dict()
automa.load_from_dict(state_dict)
```

**Important:** `load_from_snapshot` is a **classmethod** — call it on the class, not an instance.

## Persisting Local Space

By default, worker local space is cleared after `arun()` completes. Override to persist:

```python
from bridgic.asl import ASLAutoma

class StatefulAgent(ASLAutoma):
    def should_reset_local_space(self) -> bool:
        return False  # Keep local space between runs
```

## Debug Mode

```python
from bridgic.core.automa import RunningOptions

# Via constructor
agent = MyAgent(running_options=RunningOptions(debug=True, verbose=True))
```

**Note:** Top-level Automa settings override nested Automa settings (Setting Penetration Mechanism).
