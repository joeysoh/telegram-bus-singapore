import time
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
from mcpclient import MCPClient

handler = RotatingFileHandler(
    "app.log", 
    maxBytes=2* (1024*1024),    # Rollover when the file reaches 2Meg
    backupCount=5
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

 
# GROQ_MODEL = "qwen/qwen3-32b" 
# GROQ_MODEL = "qwen/qwen3.6-27b"
# GROQ_MODEL = "llama-3.3-70b-versatile"
# GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# GROQ_MODEL = "openai/gpt-oss-120b"     # flagship, reasoning + built-in tools, replaces llama-3.3-70b
# GROQ_MODEL = "openai/gpt-oss-20b"      # smaller/faster, replaces llama-3.1-8b-instant
# GROQ_MODEL = "moonshotai/kimi-k2-instruct-0905"  # strong tool-calling / structured output support

GROQ_MODEL = "openai/gpt-oss-120b"

def extractTag(text,tag):    
    pattern = rf'<{tag}>((?:(?!<{tag}>).)*?)</{tag}>'#'<answer>1<answer>2</answer>' as 2
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        logger.debug(f"Extracted: {matches[-1]}")
        return matches[-1]
    return ""
 
async def llm_response_groq(
    mcp: MCPClient,
    groq_client: Groq,
    user_prompt: str,
    system_prompt: str,
    max_tool_rounds: int = 2,#2nd call if first one has parameter error
) -> str:
    """
    Runs a full tool-calling loop against Groq, using the *already connected*
    MCPClient. Supports multiple rounds in case the model wants to chain
    several tool calls before giving a final answer.
    """
    groq_tools = mcp.to_groq_tools()
 
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    for _ in range(max_tool_rounds):
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=groq_tools,
            tool_choice="auto",
            max_completion_tokens=4096,
            # reasoning_effort= 'none'
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
                logger.debug(f"tool:{tool_name} args:{tool_args}")        
                tool_result_text = await mcp.call_tool(tool_name, tool_args)
                logger.debug(f"result: {tool_result_text}")
            except Exception as e:
                tool_result_text = f"Error calling tool '{tool_name}': {e}"
            
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result_text,
                }
            )
        time.sleep(1)
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
        answer = await llm_response_groq(mcp, groq_client, msg, system)
        logger.debug(answer)
        extracted = extractTag(answer,"answer")
        print(extracted)
        return extracted
    finally:
        await mcp.close()
        print("MCP connection closed.")
 
 
if __name__ == "__main__":
    qn = "what are the arrival times of bus stop 93131?"
    asyncio.run(message(qn))