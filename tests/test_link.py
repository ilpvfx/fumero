from textwrap import dedent

import griffe
import pytest

from fumero.config import Config
from fumero.link import LinkTable, expand_self


@pytest.fixture
def table() -> LinkTable:
    modules = {
        "__init__.py": dedent('''
            """An example package."""

            __all__ = ["Client", "core"]


            class Client:
                """A connection."""

                host: str = "localhost"

                def close(self) -> None: ...

                class Options:
                    """How to connect."""

                    def apply(self) -> None: ...
        '''),
        "core.py": dedent('''
            """The core module."""

            __all__ = ["connect"]

            TIMEOUT = 1.0


            def connect() -> None: ...
        '''),
    }

    with griffe.temporary_visited_package(
        "example", modules, docstring_parser=griffe.Parser.google
    ) as package:
        return LinkTable.collect(package, Config(base_url="/api"))


@pytest.mark.parametrize(
    "path, expected",
    [
        pytest.param("example.Client", "/api/example/Client", id="qualified class"),
        pytest.param("Client", "/api/example/Client", id="bare class"),
        pytest.param("Client.close", "/api/example/Client#close", id="method"),
        pytest.param("Client.host", "/api/example/Client#host", id="attribute"),
        pytest.param("Client.Options", "/api/example/Client/Options", id="nested class"),
        pytest.param("Options.apply", "/api/example/Client/Options#apply", id="nested member"),
        pytest.param("core", "/api/example/core", id="submodule"),
        pytest.param("example.core.connect", "/api/example/core#connect", id="module function"),
        pytest.param("core.TIMEOUT", "/api/example/core#TIMEOUT", id="module attribute"),
        pytest.param("Missing.gone", None, id="nothing documented"),
    ],
)
def test_resolve(table: LinkTable, path: str, expected: str | None):
    assert table.resolve(path) == expected


def test_resolve_tries_the_scope_before_the_package(table: LinkTable):
    assert table.resolve("close") is None
    assert table.resolve("close", scope="Client") == "/api/example/Client#close"


@pytest.mark.parametrize(
    "path, scope, expected",
    [
        pytest.param("self", "Client", "/api/example/Client", id="the page itself"),
        pytest.param("self.close", "Client", "/api/example/Client#close", id="a member of it"),
        pytest.param("self.close", None, None, id="no page to stand for"),
    ],
)
def test_resolve_a_self_path(table: LinkTable, path: str, scope: str | None, expected: str | None):
    assert table.resolve(path, scope) == expected


@pytest.mark.parametrize(
    "annotation, scope, expected",
    [
        pytest.param(
            "list[Client] | None", None, {"Client": "/api/example/Client"}, id="documented type"
        ),
        pytest.param("Client", "Client", None, id="the page it is written on"),
        pytest.param("int", None, None, id="nothing documented"),
        pytest.param(None, None, None, id="no annotation"),
    ],
)
def test_types_in(
    table: LinkTable, annotation: str | None, scope: str | None, expected: dict[str, str] | None
):
    assert table.types_in(annotation, scope) == expected


@pytest.mark.parametrize(
    "path, scope, expected",
    [
        pytest.param("self", "Client", "Client", id="the page itself"),
        pytest.param("self.close", "Client", "Client.close", id="a member of it"),
        pytest.param("Client.close", "Client", "Client.close", id="not a self path"),
        pytest.param("self.close", None, "self.close", id="no page to stand for"),
    ],
)
def test_expand_self(path: str, scope: str | None, expected: str):
    assert expand_self(path, scope) == expected
