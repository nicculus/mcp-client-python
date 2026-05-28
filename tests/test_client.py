"""Unit tests for MCPClient."""
import asyncio

import pytest

from mcp_client.client import MCPClient
from tests.conftest import (
    make_call_result,
    make_prompt,
    make_prompt_message,
    make_resource,
    make_resource_content,
    make_tool,
    mock_mcp_session,
)


@pytest.fixture
def client() -> MCPClient:
    return MCPClient(endpoint="https://example.com/mcp", headers={"x-api-key": "test-key"})


class TestListTools:
    def test_returns_tools(self, client):
        tools = [make_tool("tool_a", "Does A"), make_tool("tool_b", "Does B")]
        with mock_mcp_session(tools=tools):
            result = asyncio.run(client.list_tools())
        assert result == tools

    def test_returns_empty_list_when_no_tools(self, client):
        with mock_mcp_session(tools=[]):
            result = asyncio.run(client.list_tools())
        assert result == []

    def test_passes_endpoint_to_transport(self):
        client = MCPClient(endpoint="https://my-server.example.com/mcp")
        with mock_mcp_session() as (mock_transport_fn, _):
            asyncio.run(client.list_tools())
        mock_transport_fn.assert_called_once_with(
            "https://my-server.example.com/mcp", headers={}
        )

    def test_passes_headers_to_transport(self):
        client = MCPClient(
            endpoint="https://example.com/mcp",
            headers={"x-api-key": "secret", "X-Custom": "foo"},
        )
        with mock_mcp_session() as (mock_transport_fn, _):
            asyncio.run(client.list_tools())
        mock_transport_fn.assert_called_once_with(
            "https://example.com/mcp",
            headers={"x-api-key": "secret", "X-Custom": "foo"},
        )

    def test_defaults_to_empty_headers(self):
        client = MCPClient(endpoint="https://example.com/mcp")
        with mock_mcp_session() as (mock_transport_fn, _):
            asyncio.run(client.list_tools())
        _, call_kwargs = mock_transport_fn.call_args
        assert call_kwargs["headers"] == {}

    def test_initializes_session(self, client):
        with mock_mcp_session() as (_, mock_session):
            asyncio.run(client.list_tools())
        mock_session.initialize.assert_called_once()


class TestCallTool:
    def test_returns_result(self, client):
        expected = make_call_result("some output")
        with mock_mcp_session(call_result=expected):
            result = asyncio.run(client.call_tool("my_tool"))
        assert result is expected

    def test_passes_tool_name(self, client):
        with mock_mcp_session() as (_, mock_session):
            asyncio.run(client.call_tool("get_repo_summary"))
        mock_session.call_tool.assert_called_once_with("get_repo_summary", {})

    def test_passes_arguments(self, client):
        args = {"repo_url": "https://github.com/owner/repo"}
        with mock_mcp_session() as (_, mock_session):
            asyncio.run(client.call_tool("get_repo_summary", args))
        mock_session.call_tool.assert_called_once_with("get_repo_summary", args)

    def test_defaults_arguments_to_empty_dict(self, client):
        with mock_mcp_session() as (_, mock_session):
            asyncio.run(client.call_tool("my_tool"))
        _, call_args = mock_session.call_tool.call_args
        # second positional arg is the arguments dict
        assert mock_session.call_tool.call_args.args[1] == {}

    def test_initializes_session(self, client):
        with mock_mcp_session() as (_, mock_session):
            asyncio.run(client.call_tool("my_tool"))
        mock_session.initialize.assert_called_once()


class TestListResources:
    def test_returns_resources(self, client):
        resources = [make_resource("server://info", "Server info"), make_resource("config://region")]
        with mock_mcp_session(resources=resources):
            result = asyncio.run(client.list_resources())
        assert result == resources

    def test_returns_empty_list_when_no_resources(self, client):
        with mock_mcp_session(resources=[]):
            result = asyncio.run(client.list_resources())
        assert result == []

    def test_passes_endpoint_to_transport(self):
        client = MCPClient(endpoint="https://my-server.example.com/mcp")
        with mock_mcp_session() as (mock_transport_fn, _):
            asyncio.run(client.list_resources())
        mock_transport_fn.assert_called_once_with(
            "https://my-server.example.com/mcp", headers={}
        )

    def test_initializes_session(self, client):
        with mock_mcp_session() as (_, mock_session):
            asyncio.run(client.list_resources())
        mock_session.initialize.assert_called_once()

    def test_calls_list_resources_on_session(self, client):
        with mock_mcp_session() as (_, mock_session):
            asyncio.run(client.list_resources())
        mock_session.list_resources.assert_called_once()


class TestReadResource:
    def test_returns_contents(self, client):
        contents = [make_resource_content("server://info", '{"name":"demo"}')]
        with mock_mcp_session(resource_contents=contents):
            result = asyncio.run(client.read_resource("server://info"))
        assert result == contents

    def test_passes_uri_to_session(self, client):
        with mock_mcp_session() as (_, mock_session):
            asyncio.run(client.read_resource("config://region"))
        called_uri = mock_session.read_resource.call_args.args[0]
        assert str(called_uri) == "config://region"

    def test_returns_empty_list_when_no_contents(self, client):
        with mock_mcp_session(resource_contents=[]):
            result = asyncio.run(client.read_resource("server://info"))
        assert result == []

    def test_initializes_session(self, client):
        with mock_mcp_session() as (_, mock_session):
            asyncio.run(client.read_resource("server://info"))
        mock_session.initialize.assert_called_once()


class TestListPrompts:
    def test_returns_prompts(self, client):
        prompts = [make_prompt("analyze_endpoint", "Analyze an endpoint")]
        with mock_mcp_session(prompts=prompts):
            result = asyncio.run(client.list_prompts())
        assert result == prompts

    def test_returns_empty_list_when_no_prompts(self, client):
        with mock_mcp_session(prompts=[]):
            result = asyncio.run(client.list_prompts())
        assert result == []

    def test_initializes_session(self, client):
        with mock_mcp_session() as (_, mock_session):
            asyncio.run(client.list_prompts())
        mock_session.initialize.assert_called_once()

    def test_calls_list_prompts_on_session(self, client):
        with mock_mcp_session() as (_, mock_session):
            asyncio.run(client.list_prompts())
        mock_session.list_prompts.assert_called_once()


class TestGetPrompt:
    def test_returns_messages(self, client):
        messages = [make_prompt_message("user", "Analyze...")]
        with mock_mcp_session(prompt_messages=messages):
            result = asyncio.run(client.get_prompt("analyze_endpoint", {"url": "https://example.com"}))
        assert result == messages

    def test_passes_name_and_arguments(self, client):
        with mock_mcp_session() as (_, mock_session):
            asyncio.run(client.get_prompt("analyze_endpoint", {"url": "https://example.com"}))
        mock_session.get_prompt.assert_called_once_with(
            "analyze_endpoint", {"url": "https://example.com"}
        )

    def test_passes_none_when_no_arguments(self, client):
        with mock_mcp_session() as (_, mock_session):
            asyncio.run(client.get_prompt("analyze_endpoint"))
        mock_session.get_prompt.assert_called_once_with("analyze_endpoint", None)

    def test_returns_empty_list_when_no_messages(self, client):
        with mock_mcp_session(prompt_messages=[]):
            result = asyncio.run(client.get_prompt("analyze_endpoint"))
        assert result == []

    def test_initializes_session(self, client):
        with mock_mcp_session() as (_, mock_session):
            asyncio.run(client.get_prompt("analyze_endpoint"))
        mock_session.initialize.assert_called_once()
