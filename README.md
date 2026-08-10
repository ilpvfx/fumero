<div align="center">
  <h1>Fumero</h1>
  <p><strong>Generate a Fumadocs API reference from a Python module.</strong></p>
</div>

Fumero reads an importable module with [griffe](https://mkdocstrings.github.io/griffe/) and writes
a [Fumadocs](https://fumadocs.dev) API reference: one page per module and one per class, alongside
the React components that render them.

The reference is generated from the code. Signatures, type annotations and default values are read
from the source, and the prose is taken from the docstrings. Nothing is restated by hand, so the
reference cannot fall out of step with the code it documents.

## Install

```sh
uv add fumero --dev  # or pip install fumero
```

## Quick start

Install the components into the docs app that will render the output:

```sh
fumero init src/components/mdx
```

Register them once, so every generated page knows how to render itself:

```tsx
// src/mdx-components.tsx
import defaultMdxComponents from 'fumadocs-ui/mdx';
import * as Pdx from '@/components/mdx/pdx-components';

export function getMDXComponents(components?: MDXComponents): MDXComponents {
  return { ...defaultMdxComponents, ...Pdx, ...components };
}
```

The loader plugin that came with them labels the sidebar entries that lead to a module:

```ts
// src/lib/source.ts
import { fumeroPlugin } from '@/components/mdx/pdx-plugin';

export const source = loader({
  plugins: [fumeroPlugin()],
  baseUrl: '/docs',
  source: docs.toFumadocsSource(),
});
```

A generated page carries its kind under `_fumero`, and Fumadocs keeps only the frontmatter its schema
names, so let the rest through:

```ts
// source.config.ts
schema: pageSchema.loose(),
```

Then document a module:

```sh
fumero generate example --output content/docs/api --base-url /api --with-meta
```

A module is read from its source, not by importing it, so documenting a package does not run it.
The exception is a module with no source to read, such as a C extension: that one is imported, and
importing it runs whatever its module-level code does. Pass `--no-inspect` to read the `.pyi` stubs
beside the binary instead, and nothing is imported at all.

## Configuration

Every option is a flag on `fumero generate` and a key in a `[tool.fumero]` table. Options that do
not change between runs belong in `pyproject.toml`:

```toml
[tool.fumero]
output = "content/docs/api"
base-url = "/api"
exclude = ["example.internal", "*.tests"]
with-meta = true
```

A flag overrides the file, which overrides the defaults.

## Documentation

The full documentation lives at [here](https://ilpvfx.github.io/fumero/). Fumero documents
itself, so the API reference there is a working example of the output as much as it is a reference.

## Development

This project uses [devenv](https://devenv.sh) to manage the development environment. It sets up
Python, uv, and everything else you need.

```sh
# Install devenv if you haven't already
# https://devenv.sh/getting-started/

# Enter the dev shell - this installs all dependencies automatically
devenv shell
```

Once you are in the shell, lint, type check, and test with:

```sh
uv run ruff check
uv run ty check
uv run pytest
```
