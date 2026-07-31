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
    parse_class,
    parse_class_definition,
    parse_docstring,
    parse_function,
    parse_function_definition,
    public_members,
    strip_module_prefix,
    strip_stdlib_prefixes,
)


@pytest.fixture
def visit() -> Callable[[str], griffe.Module]:
    def visited(source: str) -> griffe.Module:
        with griffe.temporary_visited_module(
            dedent(source), module_name="example", docstring_parser=griffe.Parser.google
        ) as module:
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


def test_public_members_leave_out_a_module_a_submodule_imports():
    # a stub that writes `import package` inside its own submodule binds the whole package there,
    # and walking that as a child leads back to the root and never terminates
    modules = {
        "__init__.py": '"""An example package."""',
        "core.py": dedent('''
            """The core module."""

            import example
            import example.core
        '''),
    }

    with griffe.temporary_visited_package("example", modules) as package:
        core = cast(griffe.Module, package.members["core"])

        assert [
            member.name for member in public_members(package, griffe.Kind.MODULE, Config())
        ] == ["core"]
        assert public_members(core, griffe.Kind.MODULE, Config()) == []


def test_public_members_keep_a_class_the_package_re_exports():
    modules = {
        "__init__.py": dedent('''
            """An example package."""

            from example.core import Client
        '''),
        "core.py": dedent('''
            """The core module."""

            class Client:
                """A connection."""
        '''),
    }

    with griffe.temporary_visited_package("example", modules) as package:
        members = public_members(package, griffe.Kind.CLASS, Config())

        assert [member.name for member in members] == ["Client"]


def test_parse_class_leaves_out_a_nested_class_it_imports():
    # a class body may import a name, and two classes importing each other would otherwise be
    # walked into one another until the recursion runs out
    modules = {
        "__init__.py": '"""An example package."""',
        "core.py": dedent('''
            """The core module."""

            class Options:
                """How to connect."""

            class Client:
                """A connection."""

                from example.core import Options
        '''),
    }

    with griffe.temporary_visited_package("example", modules) as package:
        core = cast(griffe.Module, package.members["core"])
        parsed = parse_class(cast(griffe.Class, core.members["Client"]))

        assert parsed.classes == []


def test_module_attributes_are_public_and_sorted(visit: Callable[[str], griffe.Module]):
    module = visit("""
        import pathlib

        TIMEOUT: int = 30
        ROOT: pathlib.Path = pathlib.Path(".")
        _CACHE: dict[str, str] = {}
    """)

    attributes = module_attributes(module, Config())

    assert [attribute.name for attribute in attributes] == ["ROOT", "TIMEOUT"]
    assert attributes[0].annotation == "pathlib.Path"
    assert attributes[1].value == "30"


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param(
            "class Client:\n    def __init__(self, host: str = 'localhost') -> None: ...",
            "Client(host: str = 'localhost')",
            id="constructor call",
        ),
        pytest.param("class Client: ...", "Client()", id="no constructor"),
        pytest.param(
            "class Client:\n    def __new__(cls, host: str): ...",
            "Client(host: str)",
            id="constructed through new",
        ),
        pytest.param(
            "class Client:\n"
            "    def __init__(self, host: str, port: int, timeout: float, retries: int) -> None:"
            " ...",
            "Client(\n    host: str,\n    port: int,\n    timeout: float,\n    retries: int,\n)",
            id="wrapped",
        ),
    ],
)
def test_parse_class_definition(visit: Callable[[str], griffe.Module], source: str, expected: str):
    cls = cast(griffe.Class, visit(source)["Client"])

    assert parse_class_definition(cls, width=40) == expected


def test_parse_class_records_the_call_that_builds_one(visit: Callable[[str], griffe.Module]):
    module = visit('''
        class Client:
            """A connection."""

            def __init__(self, host: str) -> None: ...
    ''')

    assert parse_class(cast(griffe.Class, module["Client"])).definition == "Client(host: str)"


def test_parse_class_lists_public_methods_sorted(visit: Callable[[str], griffe.Module]):
    module = visit('''
        class Client:
            """A connection."""

            def send(self) -> None: ...

            def close(self) -> None: ...

            def _retry(self) -> None: ...
    ''')

    parsed = parse_class(cast(griffe.Class, module["Client"]))

    assert [function.name for function in parsed.functions] == ["close", "send"]


def test_parse_class_drops_excluded_members(visit: Callable[[str], griffe.Module]):
    module = visit('''
        class Client:
            """A connection."""

            host: str = "localhost"
            port: int = 8080

            def send(self) -> None: ...

            def close(self) -> None: ...
    ''')

    parsed = parse_class(cast(griffe.Class, module["Client"]), Config(exclude=("close", "port")))

    assert [function.name for function in parsed.functions] == ["send"]
    assert [attribute.name for attribute in parsed.attributes] == ["host"]


def test_parse_class_describes_constructor_parameters_from_the_class_docstring(
    visit: Callable[[str], griffe.Module],
):
    module = visit('''
        class Client:
            """A connection.

            Args:
                host: Where to connect.
            """

            def __init__(self, host: str) -> None: ...
    ''')

    parsed = parse_class(cast(griffe.Class, module["Client"]))

    assert parsed.constructor is not None
    assert parsed.constructor.name == "__init__"
    assert [entry.description for entry in parsed.constructor.docstring.parameters] == [
        "Where to connect."
    ]


def test_parse_class_describes_dataclass_parameters_from_its_attributes(
    visit: Callable[[str], griffe.Module],
):
    module = visit('''
        from dataclasses import dataclass


        @dataclass
        class Client:
            """A connection.

            Attributes:
                host: Where to connect.
            """

            host: str = "localhost"
    ''')

    parsed = parse_class(cast(griffe.Class, module["Client"]))

    assert parsed.attributes[0].description == "Where to connect."


def test_parse_class_prefers_an_attributes_own_docstring(visit: Callable[[str], griffe.Module]):
    module = visit('''
        class Client:
            """A connection.

            Attributes:
                host: Named by the section.
            """

            host: str = "localhost"
            """Named by the attribute."""
    ''')

    parsed = parse_class(cast(griffe.Class, module["Client"]))

    assert parsed.attributes[0].description == "Named by the attribute."


def test_parse_class_without_a_constructor(visit: Callable[[str], griffe.Module]):
    module = visit('''
        class Timeout(Exception):
            """The host did not answer."""
    ''')

    assert parse_class(cast(griffe.Class, module["Timeout"])).constructor is None


def test_parse_class_collects_nested_classes(visit: Callable[[str], griffe.Module]):
    module = visit('''
        class Client:
            """A connection."""

            class Options:
                """How to connect."""

            class _Internal:
                """Not documented."""
    ''')

    parsed = parse_class(cast(griffe.Class, module["Client"]))

    assert [nested.name for nested in parsed.classes] == ["Options"]
    assert parsed.classes[0].docstring.description == "How to connect."


def test_parse_function_reads_its_signature_docstring_and_source(
    visit: Callable[[str], griffe.Module],
):
    module = visit('''
        def connect(host: str) -> None:
            """Open a connection."""
    ''')

    function = parse_function(cast(griffe.Function, module["connect"]))

    assert function.name == "connect"
    assert function.definition == "def connect(host: str) -> None"
    assert function.docstring.description == "Open a connection."
    assert function.source.startswith("def connect(host: str) -> None:")


def test_parse_docstring_takes_parameters_from_the_signature(
    visit: Callable[[str], griffe.Module],
):
    module = visit('''
        def connect(host: str, port: int = 8080, timeout: float = 1.0) -> None:
            """Open a connection.

            Args:
                timeout: Seconds to wait.
                host: Where to connect.
            """
    ''')

    docstring = parse_docstring(cast(griffe.Function, module["connect"]))

    assert docstring.description == "Open a connection."
    assert [parameter.name for parameter in docstring.parameters] == ["host", "port", "timeout"]
    assert [parameter.description for parameter in docstring.parameters] == [
        "Where to connect.",
        None,
        "Seconds to wait.",
    ]
    assert docstring.parameters[1].value == "8080"


def test_parse_docstring_describes_the_return_value(visit: Callable[[str], griffe.Module]):
    module = visit('''
        import pathlib


        def resolve() -> pathlib.Path:
            """Find the root.

            Returns:
                The directory everything is relative to.
            """
    ''')

    docstring = parse_docstring(cast(griffe.Function, module["resolve"]))

    assert docstring.returns is not None
    assert docstring.returns.annotation == "pathlib.Path"
    assert docstring.returns.description == "The directory everything is relative to."


def test_parse_docstring_records_what_a_function_raises(visit: Callable[[str], griffe.Module]):
    module = visit('''
        def connect() -> None:
            """Open a connection.

            Raises:
                TimeoutError: The host did not answer.
            """
    ''')

    docstring = parse_docstring(cast(griffe.Function, module["connect"]))

    assert [raised.annotation for raised in docstring.raises] == ["TimeoutError"]
    assert docstring.raises[0].description == "The host did not answer."


def test_parse_docstring_splits_examples_into_prose_and_code(
    visit: Callable[[str], griffe.Module],
):
    module = visit('''
        def connect() -> None:
            """Open a connection.

            Examples:
                Point it at a host.

                >>> connect()
            """
    ''')

    docstring = parse_docstring(cast(griffe.Function, module["connect"]))

    assert [admonition.kind for admonition in docstring.admonitions] == ["markdown", "example"]
    assert docstring.admonitions[0].content == "Point it at a host."
    assert docstring.admonitions[1].content == ">>> connect()"


def test_parse_docstring_keeps_an_admonition_as_a_callout(visit: Callable[[str], griffe.Module]):
    module = visit('''
        def connect() -> None:
            """Open a connection.

            Warning:
                The socket stays open.
            """
    ''')

    docstring = parse_docstring(cast(griffe.Function, module["connect"]))

    assert [admonition.kind for admonition in docstring.admonitions] == ["warning"]
    assert docstring.admonitions[0].content == "The socket stays open."


def test_parse_docstring_describes_declared_attributes(visit: Callable[[str], griffe.Module]):
    module = visit('''
        class Client:
            """A connection.

            Attributes:
                host: Where it points.
            """

            host: str = "localhost"
            port: int = 8080
            _retries: int = 3
    ''')

    docstring = parse_docstring(cast(griffe.Class, module["Client"]))

    assert [attribute.name for attribute in docstring.attributes] == ["host", "port"]
    assert docstring.attributes[0].description == "Where it points."
    assert docstring.attributes[1].description is None


def test_parse_docstring_of_an_undocumented_function_still_reads_the_signature(
    visit: Callable[[str], griffe.Module],
):
    module = visit("def connect(host: str) -> None: ...")

    docstring = parse_docstring(cast(griffe.Function, module["connect"]))

    assert docstring.description is None
    assert [parameter.name for parameter in docstring.parameters] == ["host"]
    assert docstring.returns is not None
    assert docstring.returns.annotation == "None"


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
            "def connect() -> pathlib.Path",
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
        pytest.param("builtins.int", "int", id="builtin"),
        pytest.param("pathlib.Path", "Path", id="pathlib"),
        pytest.param("typing.Optional[builtins.str]", "Optional[str]", id="nested"),
        pytest.param("collections.abc.Sequence[str]", "Sequence[str]", id="collections.abc"),
        pytest.param("datetime.datetime", "datetime", id="datetime"),
        pytest.param("griffe.Module", "griffe.Module", id="another package is left alone"),
        pytest.param("int", "int", id="unqualified"),
    ],
)
def test_strip_stdlib_prefixes(input: str, expected: str):
    assert strip_stdlib_prefixes(input) == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        pytest.param("fumero.Config", "Config", id="the documented module"),
        pytest.param("fumero.model.Module", "Module", id="one of its submodules"),
        pytest.param("list[fumero.Config]", "list[Config]", id="nested"),
        pytest.param("griffe.Module", "griffe.Module", id="another package is left alone"),
        pytest.param("fumero", "fumero", id="the module itself"),
        pytest.param("Config", "Config", id="already unqualified"),
    ],
)
def test_strip_module_prefix(input: str, expected: str):
    assert strip_module_prefix(input, "fumero") == expected
