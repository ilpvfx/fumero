from collections.abc import Callable
from pathlib import Path
from textwrap import dedent
from typing import cast

import griffe
import pytest

from fumero.config import Config
from fumero.error import ModuleNotFound
from fumero.parse import (
    load_module,
    module_attributes,
    parse_function_definition,
    public_members,
    remove_prefix,
)


@pytest.fixture
def visit() -> Callable[[str], griffe.Module]:
    def visited(source: str) -> griffe.Module:
        with griffe.temporary_visited_module(dedent(source), module_name="example") as module:
            return module

    return visited


def test_load_module_reads_a_package_on_the_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    package = tmp_path / "example"
    package.mkdir()
    _ = (package / "__init__.py").write_text('"""An example package."""')
    monkeypatch.syspath_prepend(tmp_path)

    module = load_module("example")

    assert module.name == "example"
    assert module.docstring is not None
    assert module.docstring.value == "An example package."


def test_load_module_reports_a_module_it_cannot_import():
    with pytest.raises(ModuleNotFound) as raised:
        _ = load_module("example_that_is_not_installed")

    assert raised.value.name == "example_that_is_not_installed"


@pytest.mark.parametrize(
    "kind, expected",
    [
        pytest.param(griffe.Kind.CLASS, ["Client"], id="class"),
        pytest.param(griffe.Kind.FUNCTION, ["connect"], id="function"),
        pytest.param(griffe.Kind.ATTRIBUTE, ["TIMEOUT"], id="attribute"),
    ],
)
def test_public_members_select_one_kind(
    visit: Callable[[str], griffe.Module], kind: griffe.Kind, expected: list[str]
):
    module = visit("""
        TIMEOUT = 30


        class Client: ...


        def connect() -> None: ...
    """)

    assert [member.name for member in public_members(module, kind, Config())] == expected


def test_public_members_follow_dunder_all(visit: Callable[[str], griffe.Module]):
    module = visit("""
        __all__ = ["Client"]


        class Client: ...


        class Server: ...
    """)

    members = public_members(module, griffe.Kind.CLASS, Config())

    assert [member.name for member in members] == ["Client"]


def test_public_members_treat_underscored_names_as_private(visit: Callable[[str], griffe.Module]):
    module = visit("""
        def connect() -> None: ...


        def _retry() -> None: ...
    """)

    members = public_members(module, griffe.Kind.FUNCTION, Config())

    assert [member.name for member in members] == ["connect"]


def test_public_members_drop_excluded_members(visit: Callable[[str], griffe.Module]):
    module = visit("""
        class Client: ...


        class Server: ...
    """)

    members = public_members(module, griffe.Kind.CLASS, Config(exclude=("*.Server",)))

    assert [member.name for member in members] == ["Client"]


def test_module_attributes_are_public_and_sorted(visit: Callable[[str], griffe.Module]):
    module = visit("""
        import pathlib

        TIMEOUT: int = 30
        ROOT: pathlib.Path = pathlib.Path(".")
        _CACHE: dict[str, str] = {}
    """)

    attributes = module_attributes(module, Config())

    assert [attribute.name for attribute in attributes] == ["ROOT", "TIMEOUT"]
    assert attributes[0].annotation == "Path"
    assert attributes[1].value == "30"


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param(
            "def connect(host: str) -> None: ...",
            "def connect(host: str) -> None",
            id="annotated",
        ),
        pytest.param("def connect(host): ...", "def connect(host)", id="unannotated"),
        pytest.param(
            "def connect(host: str = 'localhost'): ...",
            "def connect(host: str = 'localhost')",
            id="annotated default",
        ),
        pytest.param(
            "def connect(host='localhost'): ...",
            "def connect(host='localhost')",
            id="unannotated default",
        ),
        pytest.param(
            "def connect(*args, **kwargs): ...",
            "def connect(*args, **kwargs)",
            id="variadic",
        ),
        pytest.param(
            "def connect(host, /, port, *, timeout): ...",
            "def connect(host, /, port, *, timeout)",
            id="kind markers",
        ),
        pytest.param(
            "def connect(host, /): ...",
            "def connect(host, /)",
            id="trailing positional marker",
        ),
        pytest.param(
            "import pathlib\n\n\ndef connect() -> pathlib.Path: ...",
            "def connect() -> Path",
            id="return annotation",
        ),
    ],
)
def test_parse_function_definition(
    visit: Callable[[str], griffe.Module], source: str, expected: str
):
    function = cast(griffe.Function, visit(source)["connect"])

    assert parse_function_definition(function) == expected


def test_parse_function_definition_drops_the_receiver(visit: Callable[[str], griffe.Module]):
    module = visit("""
        class Client:
            def connect(self, host: str) -> None: ...
    """)

    function = cast(griffe.Function, module["Client.connect"])

    assert parse_function_definition(function) == "def connect(host: str) -> None"


def test_parse_function_definition_wraps_a_long_signature(
    visit: Callable[[str], griffe.Module],
):
    module = visit("""
        def connect(
            host: str, port: int, timeout: float, retries: int, backoff: float
        ) -> None: ...
    """)

    function = cast(griffe.Function, module["connect"])

    assert parse_function_definition(function) == dedent("""\
        def connect(
            host: str,
            port: int,
            timeout: float,
            retries: int,
            backoff: float,
        ) -> None""")


@pytest.mark.parametrize(
    "input, expected",
    [
        pytest.param("builtins.int", "int"),
        pytest.param("typing.Optional[builtins.str]", "Optional[str]"),
        pytest.param("pathlib.Path", "Path"),
        pytest.param("a.b.c.Class", "Class"),
        pytest.param("obj.method", "obj.method"),
        pytest.param("int", "int"),
    ],
)
def test_remove_prefix(input: str, expected: str):
    assert remove_prefix(input) == expected
