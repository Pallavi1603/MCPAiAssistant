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
        
        
    
    
    
