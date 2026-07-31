import asyncio
import os
import json
import sys
import traceback
from contextlib import AsyncExitStack
from typing import Any

from google import genai
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
   
print("GEMINI_API_KEY =", os.getenv("GEMINI_API_KEY"))

if not os.getenv("GEMINI_API_KEY"):
    print("Set GEMINI_API_KEY first.")

CONFIG_FILE= os.path.join(os.path.dirname(__file__),"config.json")
MODEL="gemini-3.5-flash"


class MultiServerMCPClient:
    
    def __init__(self):
        self.exit_stack=AsyncExitStack()
        self.sessions:dict[str,ClientSession]={}
        self.client=genai.Client()
        self.tool_to_server:dict[str,str]={}
        
        
    async def connect_to_server(
        self,
        name:str,
        command:str,
        args:list[str],
        env:dict[str,str]|None):
        merged_env={**os.environ} 
        if env:
            merged_env.update(
                {
                k:v for k,v in env.items() if v and "PUT_YOUR" not in v
                })
        
        params=StdioServerParameters(
            command=command,
            args=args,
            env=merged_env
        )
        
        stdio_transport=await self.exit_stack.enter_async_context(stdio_client(params))
        read_stream,write_stream=stdio_transport 
        session=await self.exit_stack.enter_async_context(ClientSession(read_stream,write_stream))
        
        await session.initialize()
        self.sessions[name]=session
        print(f" connected :{name} ")
        
    async def connect_all(self, config: dict):
        enabled = config.get("enabled", [])
        for name in enabled:
            server_cfg = config["servers"][name]
            try:
                await self.connect_to_server(
                name,
                server_cfg["command"],
                server_cfg["args"],
                server_cfg.get("env"),
            )
            except Exception as e:
                print(f"  failed to connect '{name}': {e}")
                    
    async def list_all_tools(self)->list[dict[str,Any]]:
        gemini_tools=[]
        for server_name,session in self.sessions.items():
            resp=await session.list_tools()
            for tool in resp.tools:
                qualified_tool_name=f"{server_name}__{tool.name}"
                self.tool_to_server[qualified_tool_name]=server_name
                gemini_tools.append(
                    {
                        "type":"function",
                        "name":qualified_tool_name,
                        "description":f"[{server_name}] {tool.description or ''}",
                        "parameters":tool.input_schema
                    }
                )
        return gemini_tools

    async def call_tool(self,qualified_tool_name:str,arguments:dict)->str:
        server_name=self.tool_to_server.get(qualified_tool_name)
        if not server_name:
            return f" Error unknown tool '{qualified_tool_name}'"
            
        real_tool_name=qualified_tool_name[len(server_name)+2:]
        server_name=self.sessions[server_name]
        result=await session.call_tool(real_tool_name,arguments)
            
        parts=[]
        for item in result.content:
            if hasattr(item,"text"):
                parts.append(item.text)
            else:
                parts.append(str(item.text))
            
        if parts:
            return "\n".join(parts)
        else:
            return ("tool returned no content")
            
    async def chat_loop(self):
        tools=await self.list_all_tools()
        print(f"\n{len(tools)} tool(s) available across {len(self.sessions)} server(s)")
            
        for t in tools:
            print(f" -{t['name']}")
        print("\n Type a message ('quit' to exit). \n")
            
        last_interaction_id=None
            
        while True:
            user_input=input("you> ").strip()
            if user_input.lower() in ("quit","exit"):
                break
            if not user_input:
                continue
                
            interaction=self.client.interactions.create(
                model=MODEL,
                input=user_input,
                tools=tools,
                previous_interaction_id=last_interaction_id
            )
                
            last_interaction_id=interaction_id
                
            while True:
                function_call_steps=[s for s in interaction_steps if s.type=="function_call"]
                    
                if not function_call_steps:
                    print(f" \n gemini {interaction.output_text}\n")
                    break
                    
                function_results=[]
                for step in function_call_steps:
                    print(f"[calling tool:{step.name}({json.dumps(step.arguments)})]")
                        
                    try:
                        output=await self.call_tool(step.name,step.arguments)
                    except Exception as e:
                        output=f"Error calling tool:{e}"
                    function_results.append({
                        "type":"function_result",
                        "name":"step.name",
                        "call_id":"step_id",
                        "result":[{"type":"text","text":output}]
                    })
                    
                    
                interaction = self.gemini.interactions.create(
                model=MODEL,
                previous_interaction_id=interaction_id,
                tools=tools,
                input=function_results,
            )
            last_interaction_id = interaction.id

async def cleanup(self):
        await self.exit_stack.aclose()
        
async def main():
        if not os.getenv("GEMINI_API_KEY"):
            print("Set GEMINI_API_KEY first. Get a free key: https://aistudio.google.com/apikey")
            sys.exit(1)
            
        with open (CONFIG_FILE) as f:
            config=json.load(f)
            
        os.makedirs("/tmp/mcp-sandbox",exist_ok=True)
        
        client=MultiServerMCPClient()
        try:
            print("Connecting to all MCP servers")
            await client.connect_all(config)
            if not client.sessions:
                print("No servers connected. Check config.json and your tokens.")
                return
            await client.chat_loop()

        except Exception:
            traceback.print_exc()
        finally:
            await client,cleanup()
            
if __name__=="__main__":
    asyncio.run(main())
            
            
        