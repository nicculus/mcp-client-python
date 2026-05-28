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


_header_option = click.option("--header", "headers", multiple=True, metavar="KEY:VALUE", help="Extra request header (repeatable).")
_json_option = click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")


@click.group()
def cli() -> None:
    """MCP client — interact with a serverless MCP server."""


@cli.group()
def tools() -> None:
    """Tool operations."""


@tools.command("list")
@_json_option
@_header_option
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
@_json_option
@_header_option
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


# --- resources ----------------------------------------------------------------

@cli.group()
def resources() -> None:
    """Resource operations."""


@resources.command("list")
@_json_option
@_header_option
def resources_list(as_json: bool, headers: tuple[str, ...]) -> None:
    """List available resources."""
    client = _build_client(headers)
    result = asyncio.run(client.list_resources())
    if as_json:
        click.echo(json.dumps([r.model_dump() for r in result], indent=2))
    else:
        if not result:
            click.echo("No resources available.")
            return
        for r in result:
            desc = f" — {r.description}" if getattr(r, "description", None) else ""
            click.echo(f"{r.uri}{desc}")


@resources.command("read")
@click.argument("uri")
@_json_option
@_header_option
def resources_read(uri: str, as_json: bool, headers: tuple[str, ...]) -> None:
    """Read a resource by URI."""
    client = _build_client(headers)
    result = asyncio.run(client.read_resource(uri))
    if as_json:
        click.echo(json.dumps([c.model_dump() if hasattr(c, "model_dump") else c for c in result], indent=2))
    else:
        for item in result:
            text = getattr(item, "text", None)
            if text is not None:
                click.echo(text)
            else:
                click.echo(json.dumps(item.model_dump() if hasattr(item, "model_dump") else item, indent=2))


# --- prompts ------------------------------------------------------------------

@cli.group()
def prompts() -> None:
    """Prompt operations."""


@prompts.command("list")
@_json_option
@_header_option
def prompts_list(as_json: bool, headers: tuple[str, ...]) -> None:
    """List available prompts."""
    client = _build_client(headers)
    result = asyncio.run(client.list_prompts())
    if as_json:
        click.echo(json.dumps([p.model_dump() for p in result], indent=2))
    else:
        if not result:
            click.echo("No prompts available.")
            return
        for p in result:
            args = getattr(p, "arguments", None) or []
            arg_parts = [a.name if getattr(a, "required", False) else f"{a.name}?" for a in args]
            sig = f"({', '.join(arg_parts)})" if arg_parts else ""
            desc = f" — {p.description}" if getattr(p, "description", None) else ""
            click.echo(f"{p.name}{sig}{desc}")


@prompts.command("get")
@click.argument("name")
@click.option("--args", "args_json", default="{}", metavar="JSON", help="Prompt arguments as a JSON object.")
@_json_option
@_header_option
def prompts_get(name: str, args_json: str, as_json: bool, headers: tuple[str, ...]) -> None:
    """Get a prompt by NAME."""
    try:
        arguments: dict[str, str] = json.loads(args_json)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid JSON for --args: {exc}") from exc

    client = _build_client(headers)
    result = asyncio.run(client.get_prompt(name, arguments or None))

    if as_json:
        click.echo(json.dumps([m.model_dump() for m in result], indent=2))
    else:
        for msg in result:
            content = msg.content
            text = getattr(content, "text", None) or json.dumps(content.model_dump() if hasattr(content, "model_dump") else content)
            click.echo(f"[{msg.role}] {text}")
