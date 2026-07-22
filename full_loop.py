import os
import asyncio
import json

from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL="gemini-3.5-flash"

async def main():
    
    if not os.environ.get("GEMINI_API_KEY"):
        print("Set the GEMINI_API_KEY environment variable to your Gemini API key.")
        return
    
    client=genai.client()
    
    server_params=StdioServerParameters(
       command="npx",
       args=["-y","@modelcontextprotocal/server-filesystem",r"C:\Users\Pallavi\mcp-sandbox"],
   )
    
    async with stdio_client(server_params) as (read_stream,write_stream):
        async with ClientSession(read_stream,write_stream) as session:
            await session.initialize()
            
            tools_response=await session.list_tools()
            
            gemini_tools=[
                {
                    "type":"function",
                    "name":"tool.name",
                    "description":"tool.description",
                    "parameters":"tool.paramters"
                }
                for tool in tools_response.tools
            ]
            
            print("Ready. Type 'quit' or 'exit' to stop.\n")
            
            while True:
                user_message=input("you>").strip()
                if user_message.lower() in ("quit","exit"):
                    break
                if not user_message:
                    continue
                
                interaction=client.interactions.create(
                    model=MODEL,
                    input=user_message,
                    tools=gemini_tools
                )
                
                function_call_step=None
                for step in interaction.steps:
                    if step.type=="function_call":
                        function_call_step=step
                        break
                
                if function_call_step is None:
                    print(f"gemini> {interaction.output_text}\n")
                    continue
                
                print(f"\n calling[{function_call_step.name} with arguments:({json.dumps(function_call_step.arguments)})]\n")
                
                tool_result=await session.call_tool(
                    function_call_step.name,
                    function_call_step.arguments
                )
                
                result_text=tool_result.context[0].text
                
                final_interaction=client.interactions.create(
                    model=MODEL,
                    previous_interaction_id=interaction_id,
                    tools=gemini_tools,
                    input=[
                        {
                            "type": "function_result",
                            "name": "function_call_step.name",
                            "call_id": "function_call_step_id",
                            "result": [{"type": "text", "text": result_text}]
                        }
                    ]
                )
                
                
                print(f"gemini> {final_interaction.output_text}\n")
                
if __name__=="__main__":
    asyncio.run(main())            
            
   
    