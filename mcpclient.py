from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    """Owns the MCP server subprocess + session for as long as the app runs.""" 
    def __init__(self, command: str, args: list[str]):
        self._command = command
        self._args = args
        self._stack = AsyncExitStack()
        self.session: ClientSession = None
        self.tools = []  # raw MCP Tool objects 
 
    async def connect(self):
        server_params = StdioServerParameters(command=self._command, args=self._args)
        read, write = await self._stack.enter_async_context(stdio_client(server_params))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()
        result = await self.session.list_tools()
        self.tools = result.tools
        return self.tools
 
    def to_groq_tools(self) -> list[dict]:
        """Convert MCP tool definitions into Groq's function-calling schema."""
        groq_tools = []
        for t in self.tools:
            groq_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or "",
                        # MCP's inputSchema is already JSON Schema, Groq expects the same.
                        "parameters": t.inputSchema or {"type": "object", "properties": {}},
                    },
                }
            )
        return groq_tools
 
    async def call_tool(self, name: str, args: dict) -> str:    
        result = await self.session.call_tool(name, args)
        # result.content is a list of content blocks (text/image/etc).
        # Flatten to a string for feeding back into the chat history.
        parts = []
        for block in result.content:
            if hasattr(block, "text"):
                parts.append(block.text)
            else:
                parts.append(str(block))
        combined = "\n".join(parts) if parts else ""
        return combined
 
    async def close(self):
        await self._stack.aclose()
 