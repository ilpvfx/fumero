"""The React components that render the generated MDX.

They ship as source rather than as an npm package, so a docs app owns them the moment they are
written. Restyle them freely: nothing here will overwrite that work on the next release.

They read the host app's own theme tokens and bring no palette of their own, so the reference
tracks the rest of the site in light and dark alike.
"""

from pathlib import Path

__all__ = ["component_source", "init"]

_COMPONENTS_PATH = Path(__file__).parent / "assets" / "pdx-components.tsx"


def component_source() -> str:
    """The component file's source text.

    Useful for putting the components somewhere [`init`] does not reach, such as into a generated
    bundle, or into a template with the imports rewritten.

    Returns:
        The `.tsx` source, exactly as it ships.
    """

    return _COMPONENTS_PATH.read_text()


def init(destination: Path | str) -> Path:
    """Write the components to `destination`, creating parent directories as needed.

    Overwrites whatever is already there, so point it at a path your docs app owns.

    Args:
        destination: Where to write the `.tsx` file.

    Returns:
        The path written to.

    Examples:
        ```python
        init("src/components/mdx/pdx.tsx")
        ```
    """

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(component_source())

    return path
