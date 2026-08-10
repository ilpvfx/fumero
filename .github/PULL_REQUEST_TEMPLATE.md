<!--
Title this pull request as a conventional commit, e.g. `fix: read a class signature from __new__`.
It becomes the commit subject on merge, and release-please reads it to decide the version bump and
write the changelog. CI checks this for you.
-->

### Description

Please explain the changes you made here.

### Checklist

<!--
CI runs pytest, ruff and ty on every push, so there is nothing to tick off for those. These are the
things it cannot check for you. Inside `devenv shell` the first two are git hooks and happen on
commit. Ask if any of them are unclear.
-->

- [ ] Regenerated the reference, if the output changed (`uv run fumero generate fumero`)
- [ ] Re-copied the components, if `src/fumero/assets/` changed (`uv run fumero init docs/src/components/mdx`)
- [ ] Covered new behaviour with a test
- [ ] Documented anything a user would have to know
