# MCP Integration

Connect to MCP (Model Context Protocol) servers for external tool integration.

## Installation

```bash
pip install bridgic-protocols-mcp
```

## Connection Types

| Type | Use Case |
|------|----------|
| `McpServerConnectionStdio` | Local processes via stdin/stdout (npx, python scripts) |
| `McpServerConnectionStreamableHttp` | Remote HTTP servers |

## McpToolSetBuilder (Recommended)

The simplest way to use MCP tools — creates connection internally:

```python
from bridgic.protocols.mcp import McpToolSetBuilder
from bridgic.core.agentic.recent import ReCentAutoma, StopCondition
from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration

llm = OpenAILlm(
    api_key="your-api-key",
    configuration=OpenAIConfiguration(model="gpt-4o"),
)

# Create MCP tool builder
tools = McpToolSetBuilder.stdio(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"],
    tool_names=["read_file", "write_file"],  # Optional: filter specific tools
)

# Use with ReCentAutoma — builder passed directly to tools_builders
agent = ReCentAutoma(
    llm=llm,
    tools_builders=[tools],
    stop_condition=StopCondition(max_iteration=10),
)

result = await agent.arun(goal="Read the README.md file and summarize it")
```

### Filtering Tools

```python
# Only include specific tools
tools = McpToolSetBuilder.stdio(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-everything"],
    tool_names=["read_file", "write_file", "list_directory"],
)

# Include all tools (tool_names=None or omit)
all_tools = McpToolSetBuilder.stdio(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-everything"],
)
```

## Manual Connection Management

For more control, manage connections directly:

```python
from bridgic.protocols.mcp import (
    McpServerConnectionStdio,
    McpServerConnectionStreamableHttp,
)

# Stdio connection (local process)
stdio_conn = McpServerConnectionStdio(
    name="filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/path"],
    env={"NODE_ENV": "production"},  # Optional environment vars
    request_timeout=30,              # Optional timeout in seconds
)
stdio_conn.connect()

# HTTP connection (remote server)
http_conn = McpServerConnectionStreamableHttp(
    name="remote-tools",
    url="http://localhost:8000/mcp",
    terminate_on_close=True,         # Send DELETE on close
)
http_conn.connect()

# List available tools
tools = stdio_conn.list_tools()
for tool in tools:
    print(f"Tool: {tool.tool_name}")
    print(f"  Description: {tool.tool_description}")

# Use tools directly
tool_worker = tools[0].create_worker()
result = await tool_worker.arun(file_path="/path/to/file.txt")

# Clean up
stdio_conn.disconnect()
```

## MCP Tools in GraphAutoma

```python
from bridgic.core.automa import GraphAutoma
from bridgic.protocols.mcp import McpServerConnectionStdio

connection = McpServerConnectionStdio(
    name="my-tools",
    command="python",
    args=["my_mcp_server.py"],
)
connection.connect()

automa = GraphAutoma(name="mcp-workflow")
tools = connection.list_tools()

for tool_spec in tools:
    automa.add_worker(
        key=tool_spec.tool_name,
        worker=tool_spec.create_worker(),
        is_start=True,
        is_output=True,
    )

results = await automa.arun()
```

## MCP Tools in ASLAutoma

```python
from bridgic.asl import ASLAutoma, graph
from bridgic.protocols.mcp import McpServerConnectionStdio

connection = McpServerConnectionStdio(
    name="tools",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/data"],
)
connection.connect()
tools = {t.tool_name: t.create_worker() for t in connection.list_tools()}

class FileProcessor(ASLAutoma):
    with graph as g:
        read_file = tools["read_file"]
        process = process_content
        write_file = tools["write_file"]

        +read_file >> process >> ~write_file
```

## Connection Manager

For managing multiple connections:

```python
from bridgic.protocols.mcp import McpServerConnectionManager

manager = McpServerConnectionManager.get_instance()

# Connections are automatically registered when created
connection = manager.get_connection("my-connection-name")

# Disconnect all
manager.disconnect_all()
```

## Error Handling

```python
from bridgic.protocols.mcp import McpServerConnectionError

try:
    connection = McpServerConnectionStdio(name="tools", command="invalid")
    connection.connect()
except McpServerConnectionError as e:
    print(f"Failed to connect: {e}")
```

## Connection Lifecycle Best Practice

```python
connection = McpServerConnectionStdio(name="tools", command="...")
try:
    connection.connect()
    tools = connection.list_tools()
    result = await tools[0].create_worker().arun(...)
finally:
    connection.disconnect()
```
