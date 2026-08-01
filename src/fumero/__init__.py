"""Turn a Python module into a Fumadocs API reference.

fumero reads a module with [griffe][griffe], writes the MDX a Fumadocs site renders, and ships the
React components that render it. Signatures, type annotations and default values are read from the
source, and the prose is taken from the docstrings.

### One call

```python
from pathlib import Path

import fumero

result = fumero.generate(
    "example",
    fumero.Config(output=Path("content/docs/api"), base_url="/docs/api", clean=True),
)
```

Nothing here prints and nothing exits. [`generate`] hands back a [`Result`] naming every page it
wrote and every reference it could not resolve, which leaves a build script free to decide what
that is worth:

```python
if not result.ok:
    raise SystemExit("the reference has broken links")
```

[`ModuleNotFound`] is the one error to expect. Documenting a module means importing it, so a
module that will not import is the end of the run rather than a page with gaps in it.

### A layer down

[`generate`] is two steps taken together, and they come apart when several modules are documented
into one site, or when the tree is already loaded:

```python
config = fumero.Config(base_url="/docs/api")
module = fumero.load_module("example", config)
result = fumero.Renderer(config).render(module, Path("content/docs/api"))
```

A [`LinkTable`] is collected across the whole tree before anything is written, which is what lets
a page reference a symbol whose own page is written later.

[griffe]: https://mkdocstrings.github.io/griffe/
"""

from . import error, model
from .component import component_source, init, plugin_source
from .config import Config, Dialect
from .link import LinkTable
from .mdx import encode_text
from .parse import load_module
from .render import Renderer, Result, UnresolvedLink, generate

__all__ = [
    "Config",
    "Dialect",
    "LinkTable",
    "Renderer",
    "Result",
    "UnresolvedLink",
    "component_source",
    "encode_text",
    "error",
    "generate",
    "init",
    "load_module",
    "model",
    "plugin_source",
]
