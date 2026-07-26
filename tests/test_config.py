from collections.abc import Callable
from pathlib import Path
from textwrap import dedent

import griffe
import pytest

from fumero.config import Config, Dialect


@pytest.fixture
def pyproject(tmp_path: Path) -> Callable[[str], Path]:
    def write(content: str) -> Path:
        file = tmp_path / "pyproject.toml"
        _ = file.write_text(dedent(content))

        return file

    return write


@pytest.fixture
def library() -> griffe.Module:
    source = """
        class Client: ...


        def connect() -> None: ...
    """
    with griffe.temporary_visited_module(dedent(source), module_name="library") as visited:
        return visited


def test_from_pyproject_reads_the_table(pyproject: Callable[[str], Path]):
    config = Config.from_pyproject(
        pyproject("""
            [tool.fumero]
            output = "content/docs/api"
            base-url = "/docs/api"
            dialect = "google"
            exclude = ["example.internal", "*.tests"]
            with-meta = true
        """)
    )

    assert config.output == Path("content/docs/api")
    assert config.base_url == "/docs/api"
    assert config.dialect is Dialect.GOOGLE
    assert config.exclude == ("example.internal", "*.tests")
    assert config.with_meta is True


def test_from_pyproject_ignores_keys_naming_no_field(pyproject: Callable[[str], Path]):
    config = Config.from_pyproject(
        pyproject("""
            [tool.fumero]
            palette = "monochrome"
            clean = true
        """)
    )

    assert config.clean is True


def test_from_pyproject_without_a_table_yields_the_defaults(pyproject: Callable[[str], Path]):
    assert Config.from_pyproject(pyproject('[project]\nname = "example"\n')) == Config()


def test_from_pyproject_without_a_file_yields_the_defaults(tmp_path: Path):
    assert Config.from_pyproject(tmp_path / "pyproject.toml") == Config()


def test_from_pyproject_layers_overrides_over_the_table(pyproject: Callable[[str], Path]):
    config = Config.from_pyproject(
        pyproject("""
            [tool.fumero]
            base-url = "/docs/api"
            clean = true
        """),
        base_url="/reference",
        clean=None,
    )

    assert config.base_url == "/reference"
    assert config.clean is True


def test_replace_coerces_and_leaves_the_original_alone():
    config = Config()

    assert config.replace(output="content/docs/api").output == Path("content/docs/api")
    assert config.output == Path(".")


@pytest.mark.parametrize(
    "pattern, name, expected",
    [
        pytest.param("library.Client", "Client", True, id="dotted path"),
        pytest.param("Client", "Client", True, id="short name"),
        pytest.param("library.*", "connect", True, id="glob"),
        pytest.param("Client", "connect", False, id="another member"),
    ],
)
def test_excludes(library: griffe.Module, pattern: str, name: str, expected: bool):
    assert Config(exclude=(pattern,)).excludes(library[name]) is expected


@pytest.mark.parametrize(
    "base_url, expected",
    [
        pytest.param("", "/example/core", id="site root"),
        pytest.param("/docs/api", "/docs/api/example/core", id="base url"),
        pytest.param("/docs/api/", "/docs/api/example/core", id="trailing slash"),
    ],
)
def test_href(base_url: str, expected: str):
    assert Config(base_url=base_url).href(["example", "core"]) == expected
