"""Unit tests for the CLI."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from mcp_client.cli import cli
from tests.conftest import (
    make_call_result,
    make_prompt,
    make_prompt_arg,
    make_prompt_message,
    make_resource,
    make_resource_content,
    make_tool,
)

ENDPOINT = "https://example.com/mcp"


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def invoke(runner, args, env=None, **kwargs):
    """Invoke the CLI with MCP_ENDPOINT set by default."""
    base_env = {"MCP_ENDPOINT": ENDPOINT}
    if env:
        base_env.update(env)
    return runner.invoke(cli, args, env=base_env, **kwargs)


def patched_client(tools=None, call_result=None, resources=None, resource_contents=None, prompts=None, prompt_messages=None):
    """Return a patch context for mcp_client.cli.MCPClient."""
    mock_instance = MagicMock()
    mock_instance.list_tools = AsyncMock(return_value=tools or [])
    mock_instance.call_tool = AsyncMock(
        return_value=call_result if call_result is not None else make_call_result()
    )
    mock_instance.list_resources = AsyncMock(return_value=resources or [])
    mock_instance.read_resource = AsyncMock(return_value=resource_contents or [])
    mock_instance.list_prompts = AsyncMock(return_value=prompts or [])
    mock_instance.get_prompt = AsyncMock(return_value=prompt_messages or [])
    return patch("mcp_client.cli.MCPClient", return_value=mock_instance), mock_instance


class TestToolsList:
    def test_human_output(self, runner):
        tools = [make_tool("tool_a", "Does A"), make_tool("tool_b", "Does B")]
        ctx, _ = patched_client(tools=tools)
        with ctx:
            result = invoke(runner, ["tools", "list"])
        assert result.exit_code == 0
        assert "tool_a" in result.output
        assert "Does A" in result.output
        assert "tool_b" in result.output

    def test_json_output(self, runner):
        tools = [make_tool("tool_a", "Does A")]
        ctx, _ = patched_client(tools=tools)
        with ctx:
            result = invoke(runner, ["tools", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["name"] == "tool_a"

    def test_missing_endpoint_error(self, runner):
        ctx, _ = patched_client()
        with ctx:
            result = runner.invoke(cli, ["tools", "list"], env={"MCP_ENDPOINT": ""})
        assert result.exit_code != 0
        assert "MCP_ENDPOINT" in result.output

    def test_header_flag_passed_to_client(self, runner):
        ctx, mock_instance = patched_client()
        with ctx as MockClient:
            invoke(runner, ["tools", "list", "--header", "x-api-key:mykey"])
        MockClient.assert_called_once_with(
            endpoint=ENDPOINT, headers={"x-api-key": "mykey"}
        )

    def test_multiple_header_flags(self, runner):
        ctx, _ = patched_client()
        with ctx as MockClient:
            invoke(runner, ["tools", "list", "--header", "x-api-key:k", "--header", "X-Foo:bar"])
        _, kwargs = MockClient.call_args
        assert kwargs["headers"]["x-api-key"] == "k"
        assert kwargs["headers"]["X-Foo"] == "bar"

    def test_mcp_headers_env_parsed(self, runner):
        ctx, _ = patched_client()
        with ctx as MockClient:
            invoke(runner, ["tools", "list"], env={"MCP_HEADERS": "x-api-key:secret,X-Custom:foo"})
        _, kwargs = MockClient.call_args
        assert kwargs["headers"]["x-api-key"] == "secret"
        assert kwargs["headers"]["X-Custom"] == "foo"

    def test_header_flag_overrides_env(self, runner):
        ctx, _ = patched_client()
        with ctx as MockClient:
            invoke(
                runner,
                ["tools", "list", "--header", "x-api-key:flag-key"],
                env={"MCP_HEADERS": "x-api-key:env-key"},
            )
        _, kwargs = MockClient.call_args
        assert kwargs["headers"]["x-api-key"] == "flag-key"


class TestToolsCall:
    def test_text_output(self, runner):
        call_result = make_call_result("Hello from server")
        ctx, _ = patched_client(call_result=call_result)
        with ctx:
            result = invoke(runner, ["tools", "call", "my_tool"])
        assert result.exit_code == 0
        assert "Hello from server" in result.output

    def test_json_output(self, runner):
        call_result = make_call_result("some text")
        ctx, _ = patched_client(call_result=call_result)
        with ctx:
            result = invoke(runner, ["tools", "call", "my_tool", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "content" in data

    def test_passes_tool_name(self, runner):
        ctx, mock_instance = patched_client()
        with ctx:
            invoke(runner, ["tools", "call", "get_repo_summary"])
        mock_instance.call_tool.assert_called_once()
        args, _ = mock_instance.call_tool.call_args
        assert args[0] == "get_repo_summary"

    def test_passes_args(self, runner):
        ctx, mock_instance = patched_client()
        with ctx:
            invoke(
                runner,
                ["tools", "call", "get_repo_summary",
                 "--args", '{"repo_url": "https://github.com/owner/repo"}'],
            )
        args, _ = mock_instance.call_tool.call_args
        assert args[1] == {"repo_url": "https://github.com/owner/repo"}

    def test_invalid_args_json(self, runner):
        ctx, _ = patched_client()
        with ctx:
            result = invoke(runner, ["tools", "call", "my_tool", "--args", "{bad json}"])
        assert result.exit_code != 0
        assert "Invalid JSON" in result.output

    def test_missing_endpoint_error(self, runner):
        ctx, _ = patched_client()
        with ctx:
            result = runner.invoke(
                cli, ["tools", "call", "my_tool"], env={"MCP_ENDPOINT": ""}
            )
        assert result.exit_code != 0
        assert "MCP_ENDPOINT" in result.output


class TestResourcesList:
    def test_human_output(self, runner):
        resources = [make_resource("server://info", "Server info"), make_resource("config://region", "Region config")]
        ctx, _ = patched_client(resources=resources)
        with ctx:
            result = invoke(runner, ["resources", "list"])
        assert result.exit_code == 0
        assert "server://info" in result.output
        assert "Server info" in result.output

    def test_empty_output(self, runner):
        ctx, _ = patched_client(resources=[])
        with ctx:
            result = invoke(runner, ["resources", "list"])
        assert result.exit_code == 0
        assert "No resources available." in result.output

    def test_json_output(self, runner):
        resources = [make_resource("server://info", "Server info")]
        ctx, _ = patched_client(resources=resources)
        with ctx:
            result = invoke(runner, ["resources", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["uri"] == "server://info"

    def test_header_flag_passed_to_client(self, runner):
        ctx, _ = patched_client()
        with ctx as MockClient:
            invoke(runner, ["resources", "list", "--header", "x-api-key:mykey"])
        MockClient.assert_called_once_with(
            endpoint=ENDPOINT, headers={"x-api-key": "mykey"}
        )


class TestResourcesRead:
    def test_text_output(self, runner):
        contents = [make_resource_content("server://info", '{"name":"demo"}')]
        ctx, _ = patched_client(resource_contents=contents)
        with ctx:
            result = invoke(runner, ["resources", "read", "server://info"])
        assert result.exit_code == 0
        assert '{"name":"demo"}' in result.output

    def test_json_output(self, runner):
        contents = [make_resource_content("server://info", '{"name":"demo"}')]
        ctx, _ = patched_client(resource_contents=contents)
        with ctx:
            result = invoke(runner, ["resources", "read", "server://info", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_passes_uri_to_client(self, runner):
        ctx, mock_instance = patched_client()
        with ctx:
            invoke(runner, ["resources", "read", "config://region"])
        mock_instance.read_resource.assert_called_once_with("config://region")


class TestPromptsList:
    def test_human_output(self, runner):
        prompts = [
            make_prompt("analyze_endpoint", "Analyze an endpoint", arguments=[make_prompt_arg("url"), make_prompt_arg("method", required=False)]),
        ]
        ctx, _ = patched_client(prompts=prompts)
        with ctx:
            result = invoke(runner, ["prompts", "list"])
        assert result.exit_code == 0
        assert "analyze_endpoint" in result.output
        assert "Analyze an endpoint" in result.output
        assert "url" in result.output

    def test_empty_output(self, runner):
        ctx, _ = patched_client(prompts=[])
        with ctx:
            result = invoke(runner, ["prompts", "list"])
        assert result.exit_code == 0
        assert "No prompts available." in result.output

    def test_json_output(self, runner):
        prompts = [make_prompt("analyze_endpoint", "Analyze an endpoint")]
        ctx, _ = patched_client(prompts=prompts)
        with ctx:
            result = invoke(runner, ["prompts", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["name"] == "analyze_endpoint"

    def test_optional_arg_shown_with_question_mark(self, runner):
        prompts = [make_prompt("p", arguments=[make_prompt_arg("req", required=True), make_prompt_arg("opt", required=False)])]
        ctx, _ = patched_client(prompts=prompts)
        with ctx:
            result = invoke(runner, ["prompts", "list"])
        assert "opt?" in result.output
        assert "req" in result.output


class TestPromptsGet:
    def test_human_output(self, runner):
        messages = [make_prompt_message("user", "Analyze https://example.com")]
        ctx, _ = patched_client(prompt_messages=messages)
        with ctx:
            result = invoke(runner, ["prompts", "get", "analyze_endpoint"])
        assert result.exit_code == 0
        assert "[user]" in result.output
        assert "Analyze https://example.com" in result.output

    def test_json_output(self, runner):
        messages = [make_prompt_message("user", "Analyze...")]
        ctx, _ = patched_client(prompt_messages=messages)
        with ctx:
            result = invoke(runner, ["prompts", "get", "analyze_endpoint", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["role"] == "user"

    def test_passes_name_to_client(self, runner):
        ctx, mock_instance = patched_client()
        with ctx:
            invoke(runner, ["prompts", "get", "analyze_endpoint"])
        mock_instance.get_prompt.assert_called_once()
        args, _ = mock_instance.get_prompt.call_args
        assert args[0] == "analyze_endpoint"

    def test_passes_args_to_client(self, runner):
        ctx, mock_instance = patched_client()
        with ctx:
            invoke(runner, ["prompts", "get", "analyze_endpoint", "--args", '{"url": "https://example.com"}'])
        args, _ = mock_instance.get_prompt.call_args
        assert args[1] == {"url": "https://example.com"}

    def test_invalid_args_json(self, runner):
        ctx, _ = patched_client()
        with ctx:
            result = invoke(runner, ["prompts", "get", "analyze_endpoint", "--args", "{bad}"])
        assert result.exit_code != 0
        assert "Invalid JSON" in result.output
