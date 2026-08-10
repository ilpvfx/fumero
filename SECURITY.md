# Security policy

## Supported versions

Fumero is at `0.x`. Fixes go into the next release from `main`; there are no maintenance branches
for older versions. Report against the latest release on
[PyPI](https://pypi.org/project/fumero/), or against `main`.

## Reporting a vulnerability

Report privately, not in a public issue.

Use [GitHub's private vulnerability reporting](https://github.com/ilpvfx/fumero/security/advisories/new),
which opens a draft advisory only the maintainers can see.

Include what you need to make the problem reproducible: the version, what you ran, what happened,
and what you expected instead.

## What is in scope

Fumero is a build-time tool. It reads a Python module and writes MDX files; it serves nothing,
stores nothing, and holds no credentials. The interesting boundary is what it does with the code it
is pointed at, and what it puts into the files it writes:

- **Generated MDX escaping.** The MDX fumero writes is compiled by the docs app that consumes it.
  A docstring that can break out of its context and inject arbitrary JSX into a generated page is a
  bug worth reporting, since the docstring may come from a dependency rather than from the person
  running fumero.
- **Path handling.** `--output` names a directory, and `--clean` removes the previous output under
  it. A module name or member name that makes fumero write or delete outside that directory is a
  bug worth reporting.
- **The shipped React components.** `fumero init` writes `pdx-components.tsx` and `pdx-plugin.tsx`
  into a docs app, where they render generated content. An injection reachable through them belongs
  here too.

## What is not in scope

- **Inspecting a module runs it.** A module with no source to read, such as a C extension, is
  imported so it can be read, and importing runs its module-level code. This is documented, and
  `--no-inspect` turns it off. Pointing fumero at a package you would not install is not a
  vulnerability in fumero.
- **Vulnerabilities in dependencies.** Report those upstream. If one needs a version bound here,
  open a normal issue.
- **The documentation site.** <https://ilpvfx.github.io/fumero/> is a statically exported site on
  GitHub Pages with no backend and no user data.
