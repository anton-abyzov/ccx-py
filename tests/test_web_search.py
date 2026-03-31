"""Tests for the WebSearch tool."""

import pytest

from ccx.tools.web_search import WebSearchTool, _parse_results
from ccx.tools.base import ToolContext


@pytest.fixture
def search_tool():
    return WebSearchTool()


def test_tool_properties(search_tool):
    assert search_tool.name == "web_search"
    assert search_tool.input_schema["required"] == ["query"]


def test_parse_results_empty():
    assert _parse_results("", 10) == []
    assert _parse_results("<html>no results here</html>", 10) == []


def test_parse_results_with_links():
    html = """
    <a class="result__a" href="https://example.com">Example Title</a>
    <a class="result__snippet">This is a snippet</a>
    <a class="result__a" href="https://other.com">Other</a>
    <a class="result__snippet">Other snippet</a>
    """
    results = _parse_results(html, 10)
    assert len(results) == 2
    assert results[0][0] == "Example Title"
    assert results[0][1] == "https://example.com"
    assert results[0][2] == "This is a snippet"


def test_parse_results_max_limit():
    html = """
    <a class="result__a" href="https://a.com">A</a>
    <a class="result__a" href="https://b.com">B</a>
    <a class="result__a" href="https://c.com">C</a>
    """
    results = _parse_results(html, 2)
    assert len(results) == 2


def test_parse_results_strips_html_tags():
    html = '<a class="result__a" href="https://x.com"><b>Bold</b> Title</a>'
    results = _parse_results(html, 10)
    assert results[0][0] == "Bold Title"


def test_parse_results_uddg_redirect():
    html = '<a class="result__a" href="/l/?uddg=https%3A%2F%2Freal.com%2Fpage&kh=1">Title</a>'
    results = _parse_results(html, 10)
    assert results[0][1] == "https://real.com/page"


@pytest.mark.asyncio
async def test_search_api_schema(search_tool):
    schema = search_tool.to_api_schema()
    assert schema["name"] == "web_search"
    assert "query" in schema["input_schema"]["properties"]
    assert "max_results" in schema["input_schema"]["properties"]
