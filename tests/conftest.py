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


def make_resource(uri: str = "server://info", description: str = "Server info") -> MagicMock:
    r = MagicMock()
    r.uri = uri
    r.description = description
    r.model_dump.return_value = {"uri": uri, "description": description}
    return r


def make_resource_content(uri: str = "server://info", text: str = '{"name":"demo"}') -> MagicMock:
    c = MagicMock()
    c.uri = uri
    c.text = text
    c.model_dump.return_value = {"uri": uri, "text": text}
    return c


def make_prompt_arg(name: str, required: bool = True) -> MagicMock:
    a = MagicMock()
    a.name = name
    a.required = required
    return a


def make_prompt(name: str = "analyze_endpoint", description: str = "Analyze an endpoint", arguments=None) -> MagicMock:
    p = MagicMock()
    p.name = name
    p.description = description
    p.arguments = arguments or []
    p.model_dump.return_value = {"name": name, "description": description}
    return p


def make_prompt_message(role: str = "user", text: str = "Analyze...") -> MagicMock:
    content = MagicMock()
    content.text = text
    content.model_dump.return_value = {"type": "text", "text": text}
    msg = MagicMock()
    msg.role = role
    msg.content = content
    msg.model_dump.return_value = {"role": role, "content": {"type": "text", "text": text}}
    return msg


@contextmanager
def mock_mcp_session(
    tools=None,
    call_result=None,
    resources=None,
    resource_contents=None,
    prompts=None,
    prompt_messages=None,
):
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
    mock_session.list_resources = AsyncMock(
        return_value=MagicMock(resources=resources if resources is not None else [])
    )
    mock_session.read_resource = AsyncMock(
        return_value=MagicMock(contents=resource_contents if resource_contents is not None else [])
    )
    mock_session.list_prompts = AsyncMock(
        return_value=MagicMock(prompts=prompts if prompts is not None else [])
    )
    mock_session.get_prompt = AsyncMock(
        return_value=MagicMock(messages=prompt_messages if prompt_messages is not None else [])
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
