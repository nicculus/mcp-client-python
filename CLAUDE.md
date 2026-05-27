# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Python client library and CLI for connecting to a serverless MCP server over Streamable HTTP. The companion server is [mcp-infra](https://github.com/nicculus/mcp-infra).

The package has two entrypoints:
- **Library** (`src/mcp_client/client.py`) — importable `MCPClient` class for use in other Python projects
- **CLI** (`src/mcp_client/cli.py`) — `mcp-client` binary for interactive use from the terminal

## Commands

```sh
pip install -e .          # install in editable mode
mcp-client tools list     # run the CLI
```

## Environment variables

The CLI reads these at runtime — can also be placed in a `.env` file:

| Variable | Description |
|---|---|
| `MCP_ENDPOINT` | Full URL to the MCP server (e.g. `https://YOUR_ENDPOINT/mcp`) |
| `MCP_HEADERS` | Headers as comma-separated `key:value` pairs (e.g. `"x-api-key:YOUR_KEY"`) |

## Architecture

**`src/mcp_client/client.py`** — `MCPClient` wraps the MCP Python SDK. Each public method (`list_tools`, `call_tool`) opens a fresh `streamablehttp_client` connection, initializes a `ClientSession`, executes, and closes. All methods are async.

**`src/mcp_client/cli.py`** — `click`-based CLI. Commands are namespaced under `tools` (`tools list`, `tools call <name>`). All commands accept `--json` for machine-readable output and `--header key:value` (repeatable) for custom headers. `_build_client()` merges `MCP_HEADERS` env var and `--header` flags before constructing the client.

## Conventions

- `--json` flag on every command outputs raw JSON for scripting
- Default (human) output for `tools list` is name + description; for `tools call` it prints text content directly
- Headers are the sole auth mechanism — pass `x-api-key`, `Authorization`, or whatever the server expects via `MCP_HEADERS` or `--header`
- All client methods are `async` — call them with `asyncio.run()` from synchronous code
