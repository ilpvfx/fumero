import re

_MODULE_PREFIX_RE = re.compile(r"(?:[a-z_][a-z0-9_]*\.)+([A-Z][A-Za-z0-9_]*)")


def remove_prefix(text: str) -> str:
    """Strip dotted module paths from type references (e.g. `pathlib.Path` → `Path`), relying on
    the python convention that classes are CapitalCase.
    """

    return _MODULE_PREFIX_RE.sub(r"\1", text.replace("builtins.", ""))
