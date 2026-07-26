"""Every failure fumero raises.

A caller who only needs to know whether documentation could be produced can catch
[`FumeroException`] and ignore the rest of this module. The command line does exactly that, turning
it into a message on stderr and a non-zero exit status.
"""

__all__ = ["FumeroException", "ModuleNotFound"]


class FumeroException(Exception):
    """Base class for every exception fumero raises."""


class ModuleNotFound(FumeroException):
    """A module could not be imported, so there is nothing to document.

    Raised by [`load_module`]. Reading a module means importing it, so it has to be installed in
    the environment fumero runs in. Sitting in a directory nearby is not enough.

    Attributes:
        name: The module path that could not be imported.
    """

    def __init__(self, name: str) -> None:
        self.name: str = name
        super().__init__(f"could not load '{name}'. Is it importable in this environment?")
