# mcp-client-python

A Python client library and CLI for connecting to a serverless MCP server over Streamable HTTP.

Companion to [mcp-infra](https://github.com/nicculus/mcp-infra), which deploys the server to AWS, Azure, or GCP.

## Installation

```sh
pip install mcp-client-python
```

## CLI

```sh
export MCP_ENDPOINT=https://YOUR_ENDPOINT/mcp
export MCP_HEADERS="x-api-key:YOUR_KEY"

# List available tools
mcp-client tools list

# Call a tool
mcp-client tools call <name> --args '{"key": "value"}'

# Machine-readable output
mcp-client tools list --json
mcp-client tools call <name> --args '{"key": "value"}' --json

# Custom headers (repeatable)
mcp-client tools list --header "x-api-key:YOUR_KEY"
mcp-client tools list --header "Authorization:Bearer tok123" --header "X-Custom:foo"
```

Credentials can also be placed in a `.env` file in the working directory. Additional headers can be set via `MCP_HEADERS` as comma-separated `key:value` pairs:

```sh
MCP_HEADERS="x-api-key:YOUR_KEY,X-Custom:foo"
```

## SDK

```python
import asyncio
from mcp_client import MCPClient

client = MCPClient(
    endpoint="https://YOUR_ENDPOINT/mcp",
    headers={"x-api-key": "YOUR_KEY"},
)

# List available tools
tools = asyncio.run(client.list_tools())
print([t.name for t in tools])

# Call a tool
result = asyncio.run(client.call_tool(
    "get_repo_summary",
    {"repo_url": "https://github.com/anthropics/anthropic-sdk-python"},
))
print(result.content)
```

Each method opens a fresh connection, executes, and closes — no persistent state to manage.

## Requirements

- Python 3.10+
- An MCP server endpoint (see [mcp-infra](https://github.com/nicculus/mcp-infra))

## License

MIT
