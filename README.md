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

### 2. Implement tool, prompt, MCP Server, start application

```python
import uvicorn
import asyncio
from typing import AsyncIterator, Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcp.schemas.tools import Tool, ToolResult, ToolResultText, ToolDefinition, ToolProgress
from mcp.schemas.prompts import Prompt, PromptDefinition, PromptsGetResult, PromptMessage, PromptMessageContentText, PromptArgument
from mcp.server import MCPServer
from mcp.router import MCPRouter


async def calculate_sum(args: dict) -> ToolResult:
    return ToolResult(content=[ToolResultText(text=str(args['a'] + args['b']))])


tool_calc = Tool(
    func=calculate_sum,
    definition=ToolDefinition(
        name="add",
        description="Adds two integers.",
        inputSchema={
            "type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"]
        }
    )
)


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


async def make_system_prompt(args: Dict[str, Any]) -> PromptsGetResult:
    return PromptsGetResult(
        description="System Instructions",
        messages=[PromptMessage(
            role="user",
            content=PromptMessageContentText(text=f"Act as a {args.get('role', 'assistant')}.")
        )]
    )


prompt_sys = Prompt(
    func=make_system_prompt,
    definition=PromptDefinition(
        name="system_persona",
        description="Generates dynamic system prompts.",
        arguments=[PromptArgument(name="role", required=False)]
    )
)


class App(FastAPI):
    def __init__(self, mcp_server: MCPServer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mcp_server = mcp_server
        self.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
        self.add_event_handler("startup", self._startup_events)

    @classmethod
    def new(cls) -> "App":
        return cls(mcp_server=MCPServer("sovereign-node-01"))

    async def _startup_events(self):
        self.mcp_server.tools.add([tool_calc, tool_stream])
        self.mcp_server.prompts.add([prompt_sys])

        for router in self._routers():
            self.include_router(router)

    def _routers(self):
        return [MCPRouter(self.mcp_server)]


def main():
    uvicorn.run(App.new(), host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
```

### 3. Test 

Test using npx @modelcontextprotocol/inspector

Choose Streamable HTTP Transport Type & Via Proxy Connection Type

```sh
npx @modelcontextprotocol/inspector http://localhost:8000/mcp
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