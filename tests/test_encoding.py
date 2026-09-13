"""Every file fumero reads or writes is UTF-8 with LF endings, whatever the platform prefers.

Left to the interpreter's default, `read_text` and `write_text` use the locale's encoding, which on
Windows is cp1252: an em dash in a docstring fails the render outright, and every file written gains
CRLF endings the docs app never asked for. Both are invisible on macOS and Linux, where the default
already is UTF-8, so the checks here are written to fail on any platform rather than to wait for a
Windows runner to notice.
"""

import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent
from typing import cast

import griffe
import pytest

from fumero.component import init
from fumero.config import Config
from fumero.render import Renderer, Result


@pytest.fixture
def package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> griffe.Module:
    source = tmp_path / "src" / "accented"
    source.mkdir(parents=True)

    _ = (source / "__init__.py").write_text(
        dedent('''
            """A package documented in prose — punctuation and all.

            Written by François Ariès, who reaches for an em dash — often — and for
            “curly quotes” whenever plain ones would do.
            """

            __all__ = ["Café"]


            class Café:
                """Serves espresso — nothing else."""
        '''),
        encoding="utf-8",
    )

    monkeypatch.syspath_prepend(tmp_path / "src")

    return cast(griffe.Module, griffe.load("accented", docstring_parser=griffe.Parser.google))


@pytest.fixture
def rendered(tmp_path: Path, package: griffe.Module) -> tuple[Path, Result]:
    output = tmp_path / "out"

    return output, Renderer(Config(output=output, with_meta=True)).render(package, output)


def test_render_writes_utf8_whatever_the_platform_prefers(rendered: tuple[Path, Result]):
    output, _ = rendered

    index = (output / "accented" / "index.mdx").read_bytes()

    assert "—".encode() in index
    assert "François Ariès".encode() in index


def test_render_writes_lf_endings_whatever_the_platform_prefers(rendered: tuple[Path, Result]):
    output, _ = rendered

    written = [path for path in sorted(output.rglob("*")) if path.is_file()]

    assert written
    for path in written:
        assert b"\r\n" not in path.read_bytes(), f"CRLF in {path.relative_to(output).as_posix()}"


def test_init_writes_lf_endings_whatever_the_platform_prefers(tmp_path: Path):
    for path in init(tmp_path / "components"):
        assert b"\r\n" not in path.read_bytes(), f"CRLF in {path.name}"


_PROBE = """
import sys
from pathlib import Path

import fumero
from fumero.component import init

output = Path(sys.argv[1])
_ = fumero.generate("fumero", fumero.Config(output=output / "api", with_meta=True))
_ = init(output / "components")
_ = fumero.Config.from_pyproject(sys.argv[2])
"""


def test_no_file_is_read_or_written_at_the_platform_default_encoding(tmp_path: Path):
    """Guards the call sites the two checks above cannot reach.

    `PYTHONWARNDEFAULTENCODING` makes the interpreter warn wherever a text file is opened without an
    explicit encoding, which is the bug itself rather than one of its symptoms. Third-party warnings
    are not ours to fix, so only the ones raised from fumero's own files count.
    """

    pyproject = tmp_path / "pyproject.toml"
    _ = pyproject.write_text('[tool.fumero]\nbase-url = "/api"\n', encoding="utf-8")

    probe = subprocess.run(
        [
            sys.executable,
            "-W",
            "always::EncodingWarning",
            "-c",
            _PROBE,
            str(tmp_path / "out"),
            str(pyproject),
        ],
        env={**os.environ, "PYTHONWARNDEFAULTENCODING": "1"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert probe.returncode == 0, probe.stderr

    offenders = [
        line
        for line in probe.stderr.splitlines()
        if "EncodingWarning" in line and f"{os.sep}fumero{os.sep}" in line
    ]

    assert offenders == []
