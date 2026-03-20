# Event Handling

Real-time communication between workers and the application layer **without interrupting execution**. For interactions requiring process persistence breaks, see `human-interaction.md`.

## Core Types

```python
from bridgic.core.automa.interaction import Event, Feedback, FeedbackSender
```

### Event

```python
from bridgic.core.automa.interaction import Event

event = Event(
    event_type="progress",       # Optional[str] - event category
    data={"step": 3, "total": 10}  # Optional[Any] - event payload
)
# Also has: timestamp: datetime (auto-set)
```

### Feedback

```python
from bridgic.core.automa.interaction import Feedback

feedback = Feedback(data="approved")
```

### FeedbackSender

Abstract class used by event handlers to send feedback back:

```python
# FeedbackSender.send(feedback: Feedback) -> None
```

### EventHandlerType

Event handlers can optionally accept a `FeedbackSender`:

```python
# Type 1: Event only
def handler(event: Event) -> None: ...

# Type 2: Event + FeedbackSender
def handler(event: Event, sender: FeedbackSender) -> None: ...
```

## Registering Event Handlers

Register on the **top-level automa** (event handlers only work on top-level):

```python
from bridgic.core.automa.interaction import Event

def handle_progress(event: Event):
    print(f"Progress: {event.data}")

automa.register_event_handler("progress", handle_progress)
```

## Posting Events (One-Way)

Workers can post events during execution without waiting for a response:

```python
import asyncio
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System
from bridgic.core.automa.interaction import Event

async def long_task(automa: GraphAutoma = System("automa")) -> str:
    for i in range(10):
        automa.post_event(Event(event_type="progress", data=i / 10))
        await asyncio.sleep(0.1)
    return "done"
```

## Requesting Feedback (Two-Way)

Workers can post events and **wait** for a response:

```python
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System
from bridgic.core.automa.interaction import Event, Feedback, FeedbackSender

# Handler that provides feedback
def handle_with_feedback(event: Event, sender: FeedbackSender):
    sender.send(Feedback(data="approved"))

automa.register_event_handler("approval", handle_with_feedback)

# Worker that requests feedback
async def approval_worker(automa: GraphAutoma = System("automa")) -> str:
    feedback = await automa.request_feedback_async(
        Event(event_type="approval", data="Need approval")
    )
    return feedback.data  # "approved"
```

**Note:** `request_feedback_async()` returns `asyncio.Future[Feedback]`. The worker is suspended until the handler calls `sender.send()`.

## Event vs Human-in-the-Loop

| Feature | Event Handling | Human-in-the-Loop |
|---------|---------------|-------------------|
| Delay tolerance | Seconds | Minutes to days |
| Process persistence | Process must stay alive | State serialized, process can terminate |
| Communication style | One-way or quick two-way | Two-way with significant delays |
| Scope | Top-level automa only | Any worker |

Use Event Handling for real-time monitoring and quick feedback loops. Use Human-in-the-Loop (see `human-interaction.md`) for interactions requiring human review time.
