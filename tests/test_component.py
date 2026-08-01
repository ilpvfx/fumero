from pathlib import Path

from fumero.component import component_source, init, plugin_source


def test_init_writes_both_files_and_makes_the_directories(tmp_path: Path):
    directory = tmp_path / "src" / "components" / "mdx"

    written = init(directory)

    assert written == [directory / "pdx-components.tsx", directory / "pdx-plugin.tsx"]
    assert (directory / "pdx-components.tsx").read_text() == component_source()
    assert (directory / "pdx-plugin.tsx").read_text() == plugin_source()


def test_the_plugin_reads_the_frontmatter_fumero_writes():
    source = plugin_source()

    assert "'_fumero' in file.data" in source
    assert "transformPageTree" in source


def test_the_components_carry_no_palette_of_their_own():
    source = component_source()

    assert "oklch(" not in source
    assert "color-mix(" not in source
    assert "--color-pdx" not in source
