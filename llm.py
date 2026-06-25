
import asyncio
import json
import os
from contextlib import AsyncExitStack
import logging
from groq import Groq
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import logging
from logging.handlers import RotatingFileHandler
import re

def extractTag(text,tag):    
    pattern = rf'<{tag}>((?:(?!<{tag}>).)*?)</{tag}>'#'<answer>1<answer>2</answer>' as 2
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        logging.debug(f"Extracted: {matches[-1]}")
        return matches[-1]
    return ""
handler = RotatingFileHandler(
    "app.log", 
    maxBytes=2* (1024*1024),    # Rollover when the file reaches 2Meg
    backupCount=5
)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[handler]
)
 
# GROQ_MODEL = "qwen/qwen3-32b" 
GROQ_MODEL = "qwen/qwen3.6-27b"
# GROQ_MODEL = "llama-3.3-70b-versatile"
# GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

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
        logging.debug(combined)
        return combined
 
    async def close(self):
        await self._stack.aclose()
 
 
async def run_with_tools_groq(
    mcp: MCPClient,
    groq_client: Groq,
    user_prompt: str,
    guardrail: str,
    max_tool_rounds: int = 1,
) -> str:
    """
    Runs a full tool-calling loop against Groq, using the *already connected*
    MCPClient. Supports multiple rounds in case the model wants to chain
    several tool calls before giving a final answer.
    """
    groq_tools = mcp.to_groq_tools()
 
    messages = [
        {"role": "system", "content": guardrail},
        {"role": "user", "content": user_prompt},
    ]
 
    for _ in range(max_tool_rounds):
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=groq_tools,
            tool_choice="auto",
            reasoning_effort= "none"
        )
 
        message = response.choices[0].message
 
        if not message.tool_calls:
            return message.content
 
        # Append the assistant turn (with tool_calls) to history.
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ],
            }
        )
 
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                tool_args = {}
 
            try:
                tool_result_text = await mcp.call_tool(tool_name, tool_args)
            except Exception as e:
                tool_result_text = f"Error calling tool '{tool_name}': {e}"
            #output
            # print(tool_result_text)
            logging.debug(tool_result_text)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result_text,
                }
            )
 
    # Ran out of max_tool_rounds; force a final answer without further tool calls.
    final = groq_client.chat.completions.create(model=GROQ_MODEL, messages=messages)
    return final.choices[0].message.content
 

async def message(msg):
    api_key = os.environ.get("GROQ")
    if not api_key:
        raise RuntimeError("Set GROQ_API_KEY in your environment before running this.")
 
    groq_client = Groq(api_key=api_key)
 
    mcp = MCPClient(command="python", args=["mcpserver.py"])
    tools = await mcp.connect()
    print(f"Connected. Discovered {len(tools)} tool(s): {[t.name for t in tools]}")

    system = open("./prompts/system.txt").read()    
 
    try:
        # Reuses session
        if True:
            user_prompt = msg
            # if user_prompt.lower() in {"exit", "quit"}:
            #     break
            answer = await run_with_tools_groq(mcp, groq_client, user_prompt, system)
            logging.debug(answer)
            # print(f"\nAssistant: {answer}")
            extracted = extractTag(answer,"answer")
            print(extracted)
            return extracted
    finally:
        await mcp.close()
        print("MCP connection closed.")
 
 
if __name__ == "__main__":
    qn = "what are the arrival times of bus stop 93131?"
    asyncio.run(message(qn))