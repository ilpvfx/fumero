"""The React components that render the generated MDX.

They ship as source rather than as an npm package, so a docs app owns them the moment they are
written. Restyle them freely: nothing here will overwrite that work on the next release.

They read the host app's own theme tokens and bring no palette of their own, so the reference
tracks the rest of the site in light and dark alike.

Two files go out. The components render the pages, and are registered in `mdx-components.tsx`. The
plugin works on the page tree the sidebar is built from, so it registers on the `loader()` instead,
and labels each generated entry with the kind of page it leads to.
"""

from pathlib import Path

__all__ = ["component_source", "init", "plugin_source"]

_ASSETS = Path(__file__).parent / "assets"


def component_source() -> str:
    """The component file's source text.

    Useful for putting the components somewhere [`init`] does not reach, such as into a generated
    bundle, or into a template with the imports rewritten.

    Returns:
        The `.tsx` source, exactly as it ships.
    """

    return (_ASSETS / "pdx-components.tsx").read_text()


def plugin_source() -> str:
    """The loader plugin's source text.

    Returns:
        The `.tsx` source, exactly as it ships.
    """

    return (_ASSETS / "pdx-plugin.tsx").read_text()


def init(directory: Path | str) -> list[Path]:
    """Write both files into `directory`, creating it and its parents as needed.

    The names are fumero's to choose, since the pages import the components by name and the two
    files are installed together and edited together.

    Overwrites whatever is already there, so point it at a directory your docs app owns.

    Args:
        directory: Where the files go, usually wherever the app keeps its MDX components.

    Returns:
        The paths written to, components first.

    Examples:
        ```python
        init("src/components/mdx")
        # [PosixPath('src/components/mdx/pdx-components.tsx'),
        #  PosixPath('src/components/mdx/pdx-plugin.tsx')]
        ```
    """

    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for name, source in (
        ("pdx-components.tsx", component_source()),
        ("pdx-plugin.tsx", plugin_source()),
    ):
        path = destination / name
        _ = path.write_text(source)
        written.append(path)

    return written
