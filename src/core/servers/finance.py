from mcp.schemas.tools import Tool, ToolResult, ToolResultText, ToolDefinition
from mcp.server import MCPServer


async def get_bitcoin_price(*args) -> ToolResult:
    return ToolResult(
        content=[
            ToolResultText(
                text="Bitcoin price is 89,123",
            )
        ]
    )


bitcoin_tool = Tool(
    func=get_bitcoin_price,
    definition=ToolDefinition(
        name="get_bitcoin_price",
        title="Bitcoin Price Checker",
        description="Retrieves the current market price of Bitcoin.",
        inputSchema={
            "type": "object",
            "properties": {
                "currency": {
                    "type": "string",
                    "description": "The fiat currency to display the price in (e.g., USD, EUR)",
                    "default": "USD"
                }
            },
            "required": []
        }
    )
)


def create_server() -> MCPServer:
    server = MCPServer("finance")

    server.tools.add([bitcoin_tool])

    return server
