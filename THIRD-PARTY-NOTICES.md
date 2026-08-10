# Third-party notices

Fumero is distributed under the MIT License; see [LICENSE](LICENSE).

This file covers third-party code that is **copied into or derived from** this repository, and
whose license asks for its notice to travel with those copies. It does not list fumero's runtime
or development dependencies. Those are installed from their own distributions, which carry their
own license files, and are named in `pyproject.toml` and `docs/package.json`.

Fumero is an independent project. It is not affiliated with, sponsored by, or endorsed by
Fumadocs.

---

## fumadocs-ui

- Upstream: <https://github.com/fuma-nama/fumadocs>
- Used in: `docs/src/layouts/docs/page/slots/breadcrumb.tsx`, a copy of the upstream
  `src/layouts/docs/page/slots/breadcrumb.tsx`, taken through the Fumadocs CLI's own eject flow so
  the breadcrumb could be restyled for this site.

```
MIT License

Copyright (c) 2023 Fuma

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## fumadocs-python

- Upstream: <https://github.com/fuma-nama/fumadocs-python>
- Used in: `src/fumero/assets/pdx-components.tsx`, which contains portions derived from it. That
  file is what `fumero init` writes into a docs app, and `docs/src/components/mdx/pdx-components.tsx`
  is this repository's own copy of it. Both carry the notice below in their header, so it travels
  with the file wherever `fumero init` puts it.

```
MIT License

Copyright (c) 2023 Fuma Nama

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Trademarks

The Important Looking Pirates name and logo (`docs/public/ilp-logo.svg`,
`docs/public/ilp-logo-black.svg`) are trademarks of Important Looking Pirates AB. The MIT License
grants no rights to use them.
