"""Shared test helpers."""
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch


def make_tool(name: str = "get_repo_summary", description: str = "Get repo info") -> MagicMock:
    tool = MagicMock()
    tool.name = name
    tool.description = description
    tool.model_dump.return_value = {"name": name, "description": description}
    return tool


def make_text_content(text: str = "result text") -> MagicMock:
    content = MagicMock()
    content.text = text
    return content


def make_call_result(text: str = "result text") -> MagicMock:
    result = MagicMock()
    result.content = [make_text_content(text)]
    result.model_dump.return_value = {"content": [{"type": "text", "text": text}]}
    return result


@contextmanager
def mock_mcp_session(tools=None, call_result=None):
    """Patch streamablehttp_client and ClientSession for client unit tests.

    Yields (mock_transport_fn, mock_session) so callers can make assertions
    about how the transport was invoked.
    """
    mock_session = AsyncMock()
    mock_session.initialize = AsyncMock()
    mock_session.list_tools = AsyncMock(
        return_value=MagicMock(tools=tools if tools is not None else [])
    )
    mock_session.call_tool = AsyncMock(
        return_value=call_result if call_result is not None else make_call_result()
    )

    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    session_cm.__aexit__ = AsyncMock(return_value=False)

    transport_cm = MagicMock()
    transport_cm.__aenter__ = AsyncMock(return_value=(MagicMock(), MagicMock(), MagicMock()))
    transport_cm.__aexit__ = AsyncMock(return_value=False)

    mock_transport_fn = MagicMock(return_value=transport_cm)

    with (
        patch("mcp_client.client.streamablehttp_client", mock_transport_fn),
        patch("mcp_client.client.ClientSession", return_value=session_cm),
    ):
        yield mock_transport_fn, mock_session
