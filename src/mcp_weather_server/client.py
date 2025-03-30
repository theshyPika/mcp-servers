import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

server_params = StdioServerParameters(
    command='python',
    args=['server.py'],
)


async def main():
    async with stdio_client(server_params) as (stdio, write):
        async with ClientSession(stdio, write) as session:
            await session.initialize()
            response = await session.list_tools()
            print(response.tools)
            response = await session.call_tool('get_weather', {'city': 'Yilan'})
            print(response)

if __name__ == '__main__':
    asyncio.run(main())