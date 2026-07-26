import json
from collections.abc import Callable
from pathlib import Path
from textwrap import dedent
from typing import Any, cast

import griffe
import pytest

from fumero.config import Config
from fumero.render import Renderer, Result, generate


@pytest.fixture
def package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> griffe.Module:
    source = tmp_path / "src" / "example"
    source.mkdir(parents=True)

    _ = (source / "__init__.py").write_text(
        dedent('''
            """An example package."""

            __all__ = ["Client", "Failure", "Timeout", "core"]

            Timeout = float
            """How long to wait."""

            _RETRIES = 3


            class Client:
                """A connection.

                See [`Missing.gone`] for nothing at all.

                Args:
                    host: Where to connect.
                """

                def __init__(self, host: str) -> None: ...

                def close(self) -> None:
                    """Close it."""

                def _reset(self) -> None: ...

                class Options:
                    """How to connect."""

                    def apply(self) -> None:
                        """Apply them."""


            class Failure(Exception):
                """Something went wrong."""
        ''')
    )
    _ = (source / "core.py").write_text(
        dedent('''
            """The core module."""

            __all__ = ["connect"]

            TIMEOUT = 1.0


            def connect(host: str) -> Timeout:
                """Open a connection.

                Args:
                    host: Where to connect.

                Raises:
                    Failure: When it does not answer.
                """
        ''')
    )

    monkeypatch.syspath_prepend(tmp_path / "src")

    return cast(griffe.Module, griffe.load("example", docstring_parser=griffe.Parser.google))


@pytest.fixture
def render(tmp_path: Path, package: griffe.Module) -> Callable[..., tuple[Path, Result]]:
    def rendered(**options: Any) -> tuple[Path, Result]:
        output = tmp_path / "out"
        result = Renderer(Config(output=output, **options)).render(package, output)

        return output, result

    return rendered


def test_render_writes_a_page_for_each_documented_thing(
    render: Callable[..., tuple[Path, Result]],
):
    output, result = render()

    written = sorted(page.relative_to(output).as_posix() for page in result.pages)

    assert written == [
        "example/Client/Options.mdx",
        "example/Client/index.mdx",
        "example/Failure.mdx",
        "example/core.mdx",
        "example/index.mdx",
    ]


def test_render_leaves_private_members_out(render: Callable[..., tuple[Path, Result]]):
    output, _ = render()

    index = (output / "example" / "index.mdx").read_text()
    client = (output / "example" / "Client" / "index.mdx").read_text()

    assert "_RETRIES" not in index
    assert "_reset" not in client


def test_render_reports_a_link_that_matched_nothing(render: Callable[..., tuple[Path, Result]]):
    output, result = render()

    assert not result.ok
    assert [link.path for link in result.unresolved] == ["Missing.gone"]
    assert result.unresolved[0].page == output / "example" / "Client" / "index.mdx"


def test_render_links_the_types_in_a_signature(render: Callable[..., tuple[Path, Result]]):
    output, _ = render(base_url="/docs/api")

    assert 'links={{"Timeout": "/docs/api/example#Timeout"}}' in (
        output / "example" / "core.mdx"
    ).read_text()


def test_render_links_a_documented_exception_it_raises(
    render: Callable[..., tuple[Path, Result]],
):
    output, _ = render(base_url="/docs/api")

    assert '<PdxRef href={"/docs/api/example/Failure"}>Failure</PdxRef>' in (
        output / "example" / "core.mdx"
    ).read_text()


@pytest.mark.parametrize(
    "options, expected",
    [
        pytest.param({}, False, id="left out by default"),
        pytest.param({"with_source": True}, True, id="included when asked"),
    ],
)
def test_render_includes_source_only_when_asked(
    render: Callable[..., tuple[Path, Result]], options: dict[str, bool], expected: bool
):
    output, _ = render(**options)

    assert ("<PdxSource>" in (output / "example" / "core.mdx").read_text()) is expected


@pytest.mark.parametrize(
    "options, expected",
    [
        pytest.param({}, False, id="left out by default"),
        pytest.param({"with_meta": True}, True, id="written when asked"),
    ],
)
def test_render_writes_meta_only_when_asked(
    render: Callable[..., tuple[Path, Result]], options: dict[str, bool], expected: bool
):
    output, _ = render(**options)

    assert (output / "example" / "meta.json").exists() is expected


def test_render_groups_the_page_order_in_meta(render: Callable[..., tuple[Path, Result]]):
    output, _ = render(with_meta=True)

    assert json.loads((output / "example" / "meta.json").read_text()) == {
        "pages": ["---Modules---", "core", "---Classes---", "Client", "Failure"]
    }


def test_render_labels_meta_groups_only_when_there_are_two(
    render: Callable[..., tuple[Path, Result]],
):
    output, _ = render(with_meta=True)

    assert json.loads((output / "example" / "Client" / "meta.json").read_text()) == {
        "pages": ["Options"]
    }


def test_render_clean_removes_the_previous_output(render: Callable[..., tuple[Path, Result]]):
    output, _ = render()
    orphan = output / "example" / "Gone.mdx"
    _ = orphan.write_text("stale")

    _, _ = render(clean=True)

    assert not orphan.exists()
    assert (output / "example" / "index.mdx").exists()


def test_generate_loads_the_module_itself(tmp_path: Path, package: griffe.Module):
    output = tmp_path / "generated"

    result = generate("example", Config(output=output))

    assert result.pages
    assert (output / "example" / "index.mdx").exists()
