from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import Tool, CallToolResult, Resource, Prompt, PromptMessage
from pydantic import AnyUrl


class MCPClient:
    """Client for a serverless MCP server over Streamable HTTP."""

    def __init__(self, endpoint: str, headers: dict[str, str] | None = None) -> None:
        self.endpoint = endpoint
        self.headers = headers or {}

    async def list_tools(self) -> list[Tool]:
        async with streamablehttp_client(self.endpoint, headers=self.headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return result.tools

    async def call_tool(self, name: str, arguments: dict | None = None) -> CallToolResult:
        async with streamablehttp_client(self.endpoint, headers=self.headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.call_tool(name, arguments or {})

    async def list_resources(self) -> list[Resource]:
        async with streamablehttp_client(self.endpoint, headers=self.headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_resources()
                return result.resources

    async def read_resource(self, uri: str) -> list:
        async with streamablehttp_client(self.endpoint, headers=self.headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.read_resource(AnyUrl(uri))
                return result.contents

    async def list_prompts(self) -> list[Prompt]:
        async with streamablehttp_client(self.endpoint, headers=self.headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_prompts()
                return result.prompts

    async def get_prompt(self, name: str, arguments: dict[str, str] | None = None) -> list[PromptMessage]:
        async with streamablehttp_client(self.endpoint, headers=self.headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.get_prompt(name, arguments)
                return result.messages
