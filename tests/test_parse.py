import pytest

from fumero.parse import remove_prefix


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
