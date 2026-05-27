"""Unit tests for MCPClient."""
import asyncio

import pytest

from mcp_client.client import MCPClient
from tests.conftest import make_call_result, make_tool, mock_mcp_session


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
