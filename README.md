# sovereign-mcp

**sovereign-mcp** is a zero-dependency, strict implementation of the Model Context Protocol (MCP) server specification (Version `2025-11-25`).

It exists because the reference Python implementation (`FastMCP`) relies on opaque "magic" decorators and implicit global state. **sovereign-mcp** is architected for transparency and total control. It enforces strict separation of concerns, explicit state management, and direct transport adherence.

Instead of vague dictionaries, it utilizes **Pydantic** for rigid schema validation and type safety, ensuring every protocol message is formally verified before transmission.

## Core Philosophy

* **No Magic:** Rejection of implicit global state. Everything is explicitly instantiated and injected.
* **Transport Agnostic:** Logic is decoupled from the HTTP layer.
* **Deterministic Lifecycle:** Tools and Prompts are managed via strict `LifecycleManager` instances.
* **Type Safety:** Heavy use of Pydantic models for request/response validation, eliminating "stringly typed" errors.

## Technical Specifications

* **Protocol:** `2025-11-25`
* **Transport:** StreamableHTTP (Server-Sent Events for downstream updates + JSON-RPC 2.0 via HTTP POST for upstream commands).
* **Concurrency:** Built on the native `asyncio` event loop. Fully non-blocking I/O with support for both atomic `awaitable` coroutines and `AsyncIterator` generators for real-time progress streaming.

## Constraints

* **Authentication:** Not implemented. Security and auth headers are delegated to the host application (FastAPI) or infrastructure layer (e.g., Nginx, API Gateway).
* **JSON-RPC Batching:** Unsupported. All requests must be sent sequentially.

## Usage

sovereign-mcp is a library (Dev Kit), not a standalone application. You must mount it within a FastAPI host.

### 1. Install using uv

```sh
uv add git+https://github.com/v4ler11/sovereign-mcp.git
```

### 1. Define Capabilities

Capabilities are defined as standalone objects. Logic is isolated from definition.

```python
import asyncio
from typing import AsyncIterator, Dict, Any
from mcp.schemas.tools import Tool, ToolResult, ToolResultText, ToolDefinition, ToolProgress
from mcp.schemas.prompts import Prompt, PromptDefinition, PromptsGetResult, PromptMessage, PromptMessageContentText, PromptArgument


# --- Tool: Standard (Sync/Async) ---
async def calculate_sum(args: dict) -> ToolResult:
    result = args['a'] + args['b']
    return ToolResult(content=[ToolResultText(text=str(result))])

tool_calc = Tool(
    func=calculate_sum,
    definition=ToolDefinition(
        name="add",
        description="Adds two integers.",
        inputSchema={
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"]
        }
    )
)

# --- Tool: Streaming (Progress) ---
async def long_process(args: dict) -> AsyncIterator[ToolResult | ToolProgress]:
    for i in range(5):
        yield ToolProgress(progress=i, total=5, message="Processing...")
        await asyncio.sleep(0.1)
    
    yield ToolResult(content=[ToolResultText(text="Done")])

tool_stream = Tool(
    func=long_process,
    definition=ToolDefinition(
        name="process_stream",
        description="Demonstrates progress reporting.",
        inputSchema={"type": "object", "properties": {}, "required": []}
    )
)

# --- Prompt ---
async def make_system_prompt(args: Dict[str, Any]) -> PromptsGetResult:
    return PromptsGetResult(
        description="System Instructions",
        messages=[
            PromptMessage(
                role="user",
                content=PromptMessageContentText(text=f"Act as a {args.get('role', 'assistant')}.")
            )
        ]
    )

prompt_sys = Prompt(
    func=make_system_prompt,
    definition=PromptDefinition(
        name="system_persona",
        description="Generates dynamic system prompts.",
        arguments=[PromptArgument(name="role", required=False)]
    )
)
```

### 2. Server Instantiation

Compose the server by injecting capabilities

```python
from mcp.server import MCPServer

def create_server() -> MCPServer:
    server = MCPServer("node-01")
    
    # Explicit registration
    server.tools.add([tool_calc, tool_stream])
    server.prompts.add([prompt_sys])

    return server
```

### 3. Entry Point (FastAPI)

Mount the MCPRouter.

```python
from fastapi import FastAPI
from mcp.router import MCPRouter

app = FastAPI()
server = create_server()

app.include_router(MCPRouter(server=server))
```

## Protocol Compliance

| Feature             | Status | Notes                                                                        |
|:--------------------|:------:|:-----------------------------------------------------------------------------|
| **JSON-RPC 2.0**    |   ✓    | Pydantic validation.                                                         |
| **StreamableHTTP**  |   ✓    | Single endpoint. POST sends (accepts SSE/JSON)                               |
| **Tools**           |   ✓    | Async support.                                                               |
| **Prompts**         |   ✓    | Dynamic generation.                                                          |
| **Resources**       |   ✓    | URI context. No pagination.                                                  |
| **ResourceSchemas** |   ✓    | RFC 6570 templates.                                                          |
| **Progress**        |   ✓    | Tool-driven reporting.                                                       |
| **Batching**        |   X    | Unsupported.                                                                 |
| **Auth**            |   X    | Host-delegated.                                                              |


## License 

MIT