# Human-in-the-Loop

Pause execution for human input with full state serialization. The process can terminate and resume later.

## Mechanism

When a worker calls `interact_with_human()`:
1. Execution pauses immediately
2. Automa state is serialized to a `Snapshot`
3. `InteractionException` is raised with snapshot and pending interactions
4. Application layer collects human feedback (can take minutes to days)
5. Automa is restored from snapshot and resumed with feedback

## Using interact_with_human

```python
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System
from bridgic.core.automa.interaction import Event

async def approval_worker(
    data: str,
    automa: GraphAutoma = System("automa")
) -> str:
    # This raises InteractionException internally
    feedback = automa.interact_with_human(
        event=Event(event_type="approval", data=data)
    )
    # Execution continues here after resume with feedback
    if feedback.data.get("approved"):
        return data
    raise ValueError("Rejected")
```

## Core Types

```python
from bridgic.core.automa.interaction import (
    Interaction,              # Contains interaction_id and event
    InteractionFeedback,      # Contains interaction_id and data
    InteractionException,     # Raised when human input needed
)
from bridgic.core.automa import Snapshot
```

### Interaction

```python
class Interaction(BaseModel):
    interaction_id: str       # Unique ID for matching feedback
    event: Event              # The event requesting human input
```

### InteractionFeedback

```python
class InteractionFeedback(Feedback):
    interaction_id: str       # Must match Interaction.interaction_id
    # data: Any               # Inherited from Feedback
```

### InteractionException

```python
class InteractionException(Exception):
    @property
    def interactions(self) -> List[Interaction]:
        """List of pending interactions requiring feedback"""
        ...

    @property
    def snapshot(self) -> Snapshot:
        """Serialized automa state for later resume"""
        ...
```

## Handling InteractionException

```python
from bridgic.core.automa.interaction import InteractionException, InteractionFeedback

try:
    result = await automa.arun(input="data")
except InteractionException as e:
    # e.interactions: List[Interaction] - pending interactions
    # e.snapshot: Snapshot - serialized automa state

    # Save snapshot for later (e.g., to database)
    snapshot = e.snapshot

    # Collect human feedback asynchronously...
    user_response = await collect_user_input()

    # Resume execution (load_from_snapshot is a CLASSMETHOD)
    restored_automa = MyAutomaClass.load_from_snapshot(snapshot)
    result = await restored_automa.arun(
        feedback_data=[
            InteractionFeedback(
                interaction_id=e.interactions[0].interaction_id,
                data=user_response
            )
        ]
    )
```

**Important:** `load_from_snapshot` is a **classmethod** — call it on the class, not an instance.

## Complete Example: Approval Gate

```python
from bridgic.asl import ASLAutoma, graph
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System
from bridgic.core.automa.interaction import Event, InteractionException, InteractionFeedback

async def approval_gate(
    data: dict,
    automa: GraphAutoma = System("automa")
) -> dict:
    feedback = automa.interact_with_human(
        event=Event(
            event_type="approval",
            data={"message": "Please review", "payload": data}
        )
    )
    if feedback.data.get("approved"):
        automa.ferry_to("execute", data=data)
    else:
        automa.ferry_to("cancel", reason=feedback.data.get("reason"))
    return data

class ApprovalAgent(ASLAutoma):
    with graph as g:
        prepare = prepare_action
        approve = approval_gate
        execute = execute_action
        cancel = cancel_action

        +prepare >> approve
        ~execute, ~cancel

# Usage
agent = ApprovalAgent()
try:
    result = await agent.arun(data={"action": "deploy"})
except InteractionException as e:
    # Present to user...
    restored = ApprovalAgent.load_from_snapshot(e.snapshot)
    result = await restored.arun(
        feedback_data=[
            InteractionFeedback(
                interaction_id=e.interactions[0].interaction_id,
                data={"approved": True}
            )
        ]
    )
```

## Key Differences from Event Handling

- **Event Handling**: Process must stay alive; for real-time communication (seconds)
- **Human-in-the-Loop**: Process can terminate; for long-duration interactions (minutes to days)
- **InteractionException cannot be suppressed** by WorkerCallbacks
