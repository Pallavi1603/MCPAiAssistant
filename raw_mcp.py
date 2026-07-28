import asyncio
from mcp import StdioServerParameters,ClientSession
from mcp.client.stdio import stdio_client


async def main():
    
    server_params=StdioServerParameters(
        command="npx",
        args=["-y","@modelcontextprotocol/server-filesystem",r"C:\Users\Pallavi\mcp-sandbox",],
    )

    async with stdio_client(server_params) as (read_stream,write_stream):
        
        async with ClientSession(read_stream,write_stream) as session:
            
            await session.initialize()
        
            tools_response=await session.list_tools()
            print("This server offers this tools")
            for tool in tools_response.tools:
                print(f"- {tool.name}: {tool.description}")

            print("\n Calling 'write file' to create a file in the mcp-sandbox")
            await session.call_tool(
                "write_file",
                {
                    "path":r"C:\Users\Pallavi\mcp-sandbox\hello.txt",
                    "content":"Hello from MCP!"
                }
            )
        
            print("\n Calling 'read file' to read the file we just created")
            result=await session.call_tool(
                "read_text_file",
                {
                    "path":r"C:\Users\Pallavi\mcp-sandbox\hello.txt",
                }
            )
        
            print("file content:",result.content[0].text)
        
        
if __name__=="__main__":
    asyncio.run(main())
        
            



# // "filesystem":{
# //     "command":"npx",
# //     "args":["-y","@modelcontextprotocal/server-filesystem",r"C:\Users\Pallavi\mcp-sandbox"],
# //     "env":{}
# // },

# // "github":{
# //     "command":"npx",
# //     "args":["-y","@modelcontextprotocol/server-github"],
# //      "GITHUB_PERSONAL_ACCESS_TOKEN": "https://github.com/Pallavi1603/AiCodeExplainer"
# // }