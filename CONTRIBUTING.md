# Contributing

Thanks for looking. Bug reports and pull requests are both welcome.

## Reporting something

Open an [issue](https://github.com/ilpvfx/fumero/issues). For a bug, the fastest thing you can give
us is the module that reproduces it. A docstring that renders wrong is usually enough, since
fumero's tests are written against exactly that shape of input.

Security problems go to [SECURITY.md](SECURITY.md) instead, not to the issue tracker.

## Setting up

This project uses [devenv](https://devenv.sh), which installs Python, uv, node and the git hooks
for you:

```sh
devenv shell
```

If you would rather not, [uv](https://docs.astral.sh/uv/) on its own is enough for the Python side:

```sh
uv sync
```

The lock resolves against public PyPI, so nothing here needs credentials.

## Working on it

```sh
uv run pytest
uv run ruff check
uv run ruff format
uv run ty check
```

CI runs all four, plus pytest on Python 3.11, 3.12 and 3.13 across Linux and macOS. Inside
`devenv shell` the git hooks run them for you before each commit.

Fumero documents itself, and the generated pages are committed. Changing anything under
`src/fumero/` that alters the output means regenerating them:

```sh
uv run fumero generate fumero
```

Changing the shipped React components under `src/fumero/assets/` means re-copying them into the
docs app, which renders from the same files:

```sh
uv run fumero init docs/src/components/mdx
```

Both are git hooks in `devenv.nix`, so inside the dev shell they happen on commit. Outside it, run
them yourself and commit the result: nothing in CI notices that the committed pages have gone
stale. What CI does check is that fumero can document itself with no broken links, which is what
`tests/test_api.py` is for.

To see the docs site:

```sh
cd docs && npm install && npm run dev
```

## Opening a pull request

Fork the repository, branch from `main`, and open the pull request against `main`.

**Title your pull request as a [conventional commit](https://www.conventionalcommits.org).** This
matters more here than in most projects: pull requests are squash-merged with the title as the
commit subject, and release-please reads those subjects off `main` to decide the version bump and
write the changelog. A title that does not parse produces a release with a hole in it.

```
feat: link a type by what it resolves to
fix: read a class signature from __new__ when there is no __init__
docs: explain what --no-inspect does
chore: bump griffe
```

`feat:` bumps the minor version, `fix:` the patch. A `!` after the type, or a `BREAKING CHANGE:`
footer, bumps the major. `docs:`, `chore:`, `ci:`, `test:` and `refactor:` do not trigger a release.

A pull request needs one approving review and green CI to merge. If you have not contributed before,
CI will not start until a maintainer approves the run. That is GitHub's gate on first-time
contributors, not something being ignored.

## House style

Read a few files before writing new ones; most of this is easier absorbed than listed.

- Ruff formats, at 100 columns. Do not hand-format around it.
- Everything public is typed, and `ty` is not optional.
- Docstrings are the documentation, since fumero renders them. Write them for someone reading the
  reference, not for someone reading the source. Google-style `Args:`, `Returns:`, `Raises:`.
- Comments explain why, in lower case, including after a full stop.
- New behaviour comes with a test. `tests/` mirrors `src/fumero/` file for file.

## Licence

Contributions are made under the [MIT Licence](LICENSE), the same terms as the rest of the project.
