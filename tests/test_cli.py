from pathlib import Path
from textwrap import dedent

import pytest

from fumero.tools.fumero import build_parser, main


@pytest.fixture
def package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    source = tmp_path / "example"
    source.mkdir()
    _ = (source / "__init__.py").write_text(
        dedent('''
            """An example package."""

            __all__ = ["Client"]


            class Client:
                """A connection.

                See [`Missing.gone`] for nothing at all.
                """
        ''')
    )

    monkeypatch.syspath_prepend(tmp_path)
    monkeypatch.chdir(tmp_path)

    return "example"


def test_unset_flags_parse_as_none():
    arguments = build_parser().parse_args(["generate", "example"])

    assert [
        arguments.output,
        arguments.clean,
        arguments.with_source,
        arguments.with_meta,
        arguments.no_inspect,
    ] == [None, None, None, None, None]


def test_no_inspect_turns_inspection_off():
    arguments = build_parser().parse_args(["generate", "example", "--no-inspect"])

    assert arguments.no_inspect is True


def test_generate_writes_the_pages_and_says_where(
    package: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    assert main(["generate", package, "--output", "out"]) == 0
    assert (tmp_path / "out" / "example" / "Client.mdx").exists()
    assert "wrote 2 pages to out" in capsys.readouterr().out


def test_a_flag_beats_the_config_file_and_the_rest_falls_through(package: str, tmp_path: Path):
    _ = (tmp_path / "pyproject.toml").write_text(
        dedent("""
            [tool.fumero]
            output = "from-file"
            with-meta = true
        """)
    )

    assert main(["generate", package, "--output", "from-flag"]) == 0
    assert not (tmp_path / "from-file").exists()
    assert (tmp_path / "from-flag" / "example" / "meta.json").exists()


def test_generate_warns_about_a_link_that_matched_nothing(
    package: str, capsys: pytest.CaptureFixture[str]
):
    assert main(["generate", package, "--output", "out"]) == 0
    assert "warning: item link `Missing.gone`" in capsys.readouterr().err


def test_generate_reports_a_module_it_cannot_import(capsys: pytest.CaptureFixture[str]):
    assert main(["generate", "example_that_is_not_installed"]) == 1
    assert "error: could not load 'example_that_is_not_installed'" in capsys.readouterr().err


def test_init_writes_the_components(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    destination = tmp_path / "src" / "components" / "mdx" / "pdx.tsx"

    assert main(["init", str(destination)]) == 0
    assert "export function PdxRef" in destination.read_text()
    assert f"wrote {destination}" in capsys.readouterr().out
