from pathlib import Path

import pytest

from fumero.error import ModuleNotFound
from fumero.parse import load_module, remove_prefix


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
