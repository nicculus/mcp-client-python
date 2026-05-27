import asyncio
import json
import os

import click
from dotenv import load_dotenv

from .client import MCPClient

load_dotenv()


def _build_client(header_flags: tuple[str, ...]) -> MCPClient:
    endpoint = os.environ.get("MCP_ENDPOINT", "")
    if not endpoint:
        raise click.ClickException("MCP_ENDPOINT is not set")

    headers: dict[str, str] = {}

    for pair in os.environ.get("MCP_HEADERS", "").split(","):
        pair = pair.strip()
        if ":" in pair:
            k, v = pair.split(":", 1)
            headers[k.strip()] = v.strip()

    for pair in header_flags:
        if ":" not in pair:
            raise click.ClickException(f"Invalid header (expected key:value): {pair!r}")
        k, v = pair.split(":", 1)
        headers[k.strip()] = v.strip()

    return MCPClient(endpoint=endpoint, headers=headers)


@click.group()
def cli() -> None:
    """MCP client — interact with a serverless MCP server."""


@cli.group()
def tools() -> None:
    """Tool operations."""


@tools.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@click.option("--header", "headers", multiple=True, metavar="KEY:VALUE", help="Extra request header (repeatable).")
def tools_list(as_json: bool, headers: tuple[str, ...]) -> None:
    """List available tools."""
    client = _build_client(headers)
    result = asyncio.run(client.list_tools())
    if as_json:
        click.echo(json.dumps([t.model_dump() for t in result], indent=2))
    else:
        for t in result:
            click.echo(f"{t.name}  {t.description or ''}")


@tools.command("call")
@click.argument("name")
@click.option("--args", "args_json", default="{}", metavar="JSON", help="Tool arguments as a JSON object.")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@click.option("--header", "headers", multiple=True, metavar="KEY:VALUE", help="Extra request header (repeatable).")
def tools_call(name: str, args_json: str, as_json: bool, headers: tuple[str, ...]) -> None:
    """Call a tool by NAME."""
    try:
        arguments = json.loads(args_json)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid JSON for --args: {exc}") from exc

    client = _build_client(headers)
    result = asyncio.run(client.call_tool(name, arguments))

    if as_json:
        click.echo(json.dumps(result.model_dump(), indent=2))
    else:
        for block in result.content:
            if hasattr(block, "text"):
                click.echo(block.text)
