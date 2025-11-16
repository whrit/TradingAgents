from types import SimpleNamespace

import pytest

from tradingagents.dataflows.openai import _extract_response_text


def test_extract_response_text_uses_output_text_when_available():
    response = SimpleNamespace(output_text="hello world", output=[])
    assert _extract_response_text(response) == "hello world"


def test_extract_response_text_skips_outputs_without_content():
    tool_call = SimpleNamespace()  # lacks content attribute
    content_chunk = SimpleNamespace(text="final report")
    assistant_message = SimpleNamespace(content=[content_chunk])
    response = SimpleNamespace(output=[tool_call, assistant_message], output_text=None)

    assert _extract_response_text(response) == "final report"


def test_extract_response_text_raises_when_no_text():
    response = SimpleNamespace(output=[SimpleNamespace()], output_text=None)

    with pytest.raises(AttributeError):
        _extract_response_text(response)
