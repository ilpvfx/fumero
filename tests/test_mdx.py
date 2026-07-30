import pytest

from fumero.link import LinkTable
from fumero.mdx import (
    CalloutType,
    callout_type,
    encode_text,
    escape_identifier,
    fence,
    jsx_props,
    summarize,
)


@pytest.fixture
def links() -> LinkTable:
    return LinkTable(
        {
            "Client": "/api/example/Client",
            "Client.close": "/api/example/Client#close",
            "example.Client": "/api/example/Client",
        }
    )


@pytest.mark.parametrize(
    "text, expected",
    [
        pytest.param("a < b", "a \\< b", id="angle bracket"),
        pytest.param("{ a }", "\\{ a \\}", id="braces"),
        pytest.param("`a < b`", "`a < b`", id="inline code"),
        pytest.param("    a < b", "    a < b", id="indented code"),
        pytest.param("```\na < b\n```", "```\na < b\n```", id="fenced code"),
        pytest.param(None, "", id="no docstring"),
    ],
)
def test_encode_text_escapes_prose_but_not_code(links: LinkTable, text: str | None, expected: str):
    assert encode_text(text, links) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        pytest.param(
            "see [`Client.close`]",
            'see <PdxRef href="/api/example/Client#close">Client.close</PdxRef>',
            id="shortcut",
        ),
        pytest.param(
            "see [`close`](Client.close)",
            'see <PdxRef href="/api/example/Client#close" title="Client.close">close</PdxRef>',
            id="code label",
        ),
        pytest.param(
            "see [the close method](Client.close)",
            "see [the close method](/api/example/Client#close)",
            id="prose label",
        ),
        pytest.param("see `Client.close`", "see `Client.close`", id="plain code span"),
        pytest.param("see [`Missing.gone`]", "see `Missing.gone`", id="unresolved shortcut"),
        pytest.param(
            "see [the docs](https://example.com)",
            "see [the docs](https://example.com)",
            id="url",
        ),
        pytest.param("see [the page](./other)", "see [the page](./other)", id="relative path"),
    ],
)
def test_encode_text_resolves_item_links(links: LinkTable, text: str, expected: str):
    assert encode_text(text, links) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        pytest.param("[`Missing.gone`]", ["Missing.gone"], id="shortcut is reported"),
        pytest.param("[gone](Missing.gone)", [], id="label is not"),
    ],
)
def test_encode_text_reports_what_it_could_not_resolve(
    links: LinkTable, text: str, expected: list[str]
):
    missed: list[str] = []

    _ = encode_text(text, links, on_unresolved=missed.append)

    assert missed == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        pytest.param(
            "[`self`]",
            '<PdxRef href="/api/example/Client">Client</PdxRef>',
            id="the page itself",
        ),
        pytest.param(
            "[`self.close`]",
            '<PdxRef href="/api/example/Client#close">Client.close</PdxRef>',
            id="a member of it",
        ),
    ],
)
def test_encode_text_expands_a_self_path(links: LinkTable, text: str, expected: str):
    assert encode_text(text, links, scope="Client") == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        pytest.param("One line.\n\nAnd more.", "One line.", id="first paragraph only"),
        pytest.param("Wrapped over\ntwo lines.", "Wrapped over two lines.", id="breaks collapsed"),
        pytest.param(None, "", id="no docstring"),
    ],
)
def test_summarize(text: str | None, expected: str):
    assert summarize(text) == expected


@pytest.mark.parametrize(
    "props, expected",
    [
        pytest.param({"name": "close", "type": None}, 'name={"close"}', id="none is omitted"),
        pytest.param({"value": "'a'"}, "value={\"'a'\"}", id="quotes survive"),
        pytest.param(
            {"links": {"Client": "/api/example/Client"}},
            'links={{"Client": "/api/example/Client"}}',
            id="mapping",
        ),
    ],
)
def test_jsx_props(props: dict[str, object], expected: str):
    assert jsx_props(**props) == expected


@pytest.mark.parametrize(
    "kind, expected",
    [
        pytest.param("Warning", CalloutType.WARN, id="matched whatever the case"),
        pytest.param("danger", CalloutType.ERROR, id="error"),
        pytest.param("note", CalloutType.INFO, id="anything else"),
    ],
)
def test_callout_type(kind: str, expected: CalloutType):
    assert callout_type(kind) is expected


@pytest.mark.parametrize(
    "text, expected",
    [
        pytest.param("plain", "```", id="no backticks"),
        pytest.param("a `b` c", "```", id="inline code"),
        pytest.param("```\na\n```", "````", id="a fence inside"),
        pytest.param(None, "```", id="nothing to hold"),
    ],
)
def test_fence(text: str | None, expected: str):
    assert fence(text) == expected


def test_escape_identifier():
    assert escape_identifier("__init__") == "\\_\\_init\\_\\_"
