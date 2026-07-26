from pathlib import Path

from fumero.component import component_source, init


def test_init_writes_the_components_and_makes_the_directories(tmp_path: Path):
    destination = tmp_path / "src" / "components" / "mdx" / "pdx.tsx"

    written = init(destination)

    assert written == destination
    assert destination.read_text() == component_source()


def test_the_components_carry_no_palette_of_their_own():
    source = component_source()

    assert "oklch(" not in source
    assert "color-mix(" not in source
    assert "--color-pdx" not in source
