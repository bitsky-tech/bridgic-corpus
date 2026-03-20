# ASL (Agent Structure Language) Syntax

ASL is Bridgic's declarative DSL for defining complex workflows. It compiles to GraphAutoma under the hood.

## Basic Structure

```python
from bridgic.asl import ASLAutoma, graph

class MyAgent(ASLAutoma):
    with graph as g:
        # Define workers
        worker_a = function_a
        worker_b = function_b

        # Declare dependencies and flow
        +worker_a >> ~worker_b
```

The `with graph as g:` block is where all ASL declarations happen: worker assignments, dependency declarations, flow control, and settings application.

## Operators Reference

### Start Operator: `+` (Unary Plus)

Mark workers as entry points. Uses Python's `__pos__` operator.

```python
+worker_a              # worker_a is a start worker
+worker_a, +worker_b   # Both are starts
+(a & b & c)           # All become start workers
```

### Output Operator: `~` (Unary Invert)

Mark workers as output (their results are returned). Uses Python's `__invert__` operator.

```python
~worker_a              # worker_a is an output worker
~worker_a, ~worker_b   # Both contribute to result
~(a & b)               # Both a and b are outputs
```

### Sequential Operator: `>>` (Right Shift)

Create dependencies (B runs after A).

```python
a >> b       # b depends on a
a >> b >> c  # c depends on b, b depends on a
```

### Parallel Operator: `&` (Bitwise AND)

Group workers for concurrent execution.

```python
a & b       # a and b run in parallel
a & b & c   # all three run in parallel
```

When used with `>>`, all workers in the group become dependencies/dependents together.

### Settings/Data Operator: `*` (Multiplication)

Apply configuration or bind parameters to workers.

```python
from bridgic.asl import Settings, Data
from bridgic.core.automa.args import ArgsMappingRule, ResultDispatchingRule

worker_a * Settings(key="custom_key")
worker_a * Settings(args_mapping_rule=ArgsMappingRule.MERGE)
worker_a * Data(param1="value1", param2=42)
worker_a * Settings(key="named") * Data(x=10)  # Chain settings and data
```

## Combined Patterns

```python
# Linear pipeline
+a >> b >> c >> ~d

# Fan-out (one to many)
+a >> (b & c & d)       # a runs first, then b, c, d in parallel

# Fan-in (many to one) — use MERGE on receiver
(a & b & c) >> ~merge   # merge receives list of results

# Diamond
+a >> (b & c) >> ~d

# Multiple entry points
+a, +b
a >> c
b >> c
~c

# Multiple outputs
+a >> (b & c)
~b, ~c

# Independent workers (for ferry_to routing)
+router
~fast_handler, ~text_handler, ~image_handler

# Fragment (reusable sub-flow)
fragment = a >> b >> c
+start >> fragment >> ~end
```

## Settings Object

```python
from bridgic.asl import Settings
from bridgic.core.automa.args import ArgsMappingRule, ResultDispatchingRule

Settings(
    key="custom_worker_key",                            # Override worker key
    args_mapping_rule=ArgsMappingRule.MERGE,             # How args flow in
    result_dispatching_rule=ResultDispatchingRule.IN_ORDER  # How results flow out
)
```

## Data Binding

### Static Data

Bind fixed values to worker parameters:

```python
from bridgic.asl import Data

class Agent(ASLAutoma):
    with graph as g:
        greet = greeting_func * Data(name="World", greeting="Hello")
        +greet >> ~greet
```

### Dynamic Data with ASLField

Define parameters populated at runtime from automa input:

```python
from bridgic.asl import ASLField, Data

class Agent(ASLAutoma):
    with graph as g:
        process = handler * Data(items=ASLField(list))
        +process >> ~process

# Usage — items comes from arun() kwargs
agent = Agent()
result = await agent.arun(items=["a", "b", "c"])
```

### ASLField with Dispatching Rule

```python
from bridgic.asl import ASLField
from bridgic.core.automa.args import ResultDispatchingRule

ASLField(
    type=list,                                          # Type annotation (default: Any)
    default=...,                                        # Default value (... means required)
    dispatching_rule=ResultDispatchingRule.IN_ORDER      # How to dispatch to workers
)
```

## Concurrent Container

### Basic Concurrent Execution

```python
from bridgic.asl import ASLAutoma, graph, concurrent

class ParallelAgent(ASLAutoma):
    with graph as g:
        prepare = prep_function

        with concurrent():
            task_a = handler_a
            task_b = handler_b
            task_c = handler_c

        aggregate = combine_function

        +prepare >> concurrent >> ~aggregate
```

### Dynamic Concurrent Workers

Create workers dynamically based on input:

```python
from bridgic.asl import ASLAutoma, graph, concurrent, ASLField, Settings, Data
from bridgic.core.automa.args import ResultDispatchingRule

async def process_item(item: str) -> str:
    return item.upper()

class DynamicParallel(ASLAutoma):
    with graph as g:
        prepare = get_items  # Returns list of items

        with concurrent(
            items=ASLField(list, dispatching_rule=ResultDispatchingRule.IN_ORDER)
        ):
            # Lambda generates workers dynamically
            handlers = lambda items: (
                process_item * Settings(key=f"handler_{i}") * Data(item=item)
                for i, item in enumerate(items)
            )

        aggregate = combine_results

        +prepare >> concurrent >> ~aggregate
```

**Note:** Lambda for dynamic worker generation can **only** be used inside a `concurrent()` block. Using lambda directly in the `graph` block causes `ASLCompilationError`.

## Common Mistakes

### Forgetting Start/Output Markers

```python
# Wrong — no start or output, will fail!
class BadAgent(ASLAutoma):
    with graph as g:
        a = task_a
        b = task_b
        a >> b

# Correct
class GoodAgent(ASLAutoma):
    with graph as g:
        a = task_a
        b = task_b
        +a >> ~b
```

### Circular Dependencies

```python
# Wrong — circular dependency causes deadlock!
a >> b >> c >> a

# Correct — use ferry_to() for loops
async def loop_worker(automa=System("automa")):
    if condition:
        automa.ferry_to("a")  # Dynamic routing, not static dependency
```

### Expecting Dict from MERGE

```python
# Wrong — MERGE returns list, not dict!
async def handler(inputs: dict):
    for key, value in inputs.items():  # Will fail!
        ...

# Correct — MERGE returns list
async def handler(inputs: list):
    for result in inputs:  # Works!
        ...
```

### Lambda Outside Concurrent

```python
# Wrong — lambda in graph context
class BadAgent(ASLAutoma):
    with graph as g:
        dynamic = lambda items: (...)  # ASLCompilationError!

# Correct — lambda inside concurrent
class GoodAgent(ASLAutoma):
    with graph as g:
        with concurrent(...):
            dynamic = lambda items: (...)  # Works!
```
