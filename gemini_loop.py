
import os
import asyncio
import json

from google import genai
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

print("GEMINI_API_KEY =", os.getenv("GEMINI_API_KEY"))

# client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# for model in client.models.list():
#     print(model.name)

MODEL = "gemini-3.5-flash"

async def main():
    if not os.environ.get("GEMINI_API_KEY"):
        print("Set the GEMINI_API_KEY environment variable to your Gemini API key.")
        return
    
    client=genai.Client()
    
    servers_params=StdioServerParameters(
        command="npx",
        args=["-y","@modelcontextprotocol/server-filesystem",r"C:\Users\Pallavi\mcp-sandbox"]
    )
    
    async with stdio_client(servers_params) as (read_stream,write_stream):
        async with ClientSession(read_stream,write_stream) as session:
            await session.initialize()
            
            tools_response= await session.list_tools()
            gemini_tools=[
                {
                    "type":"function",
                    "name":tool.name,
                    "description":tool.description,
                    "parameters":tool.inputSchema
                }
                for tool in tools_response.tools
            ]
            
            user_message=input("What do want to do?")
            
            interaction=client.interactions.create(
                model=MODEL,
                input=user_message,
                tools=gemini_tools
                
            )
            
            found_tool_call=False;
            
            for step in interaction.steps:
                if step.type=="function_call":
                    found_tool_call=True
                    print(f"\n Gemini wants to call:{step.name}")
                    print(f"\n With arguments:{json.dumps(step.arguments)}")
                    
                    
                    result=await session.call_tool(step.name,step.arguments)
                    print(f"\n Result from the tool")
                    print(result.content[0].text)
                    
            if not found_tool_call:
                    print(f"\n Gemini says:{interaction.output_text}")

if __name__=="__main__":
    asyncio.run(main())                    
    
            


