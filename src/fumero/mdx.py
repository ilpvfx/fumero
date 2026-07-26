"""Turning docstring prose into MDX.

Two jobs. Escaping, so text holding a `<` or a `{` renders as written instead of being read as
JSX, and item links, so a docstring can point at another documented symbol by name.

Item links follow [rustdoc's linking by name][rustdoc]: they are explicit, so a plain code span is
never quietly turned into a link. See [`encode_text`] for the forms that are recognised.

[rustdoc]: https://doc.rust-lang.org/rustdoc/write-documentation/linking-to-items-by-name.html
"""

import json
import re
from collections.abc import Callable
from enum import StrEnum

from .link import LinkTable, expand_self

__all__ = [
    "CalloutType",
    "callout_type",
    "encode_text",
    "escape_identifier",
    "fence",
    "jsx_props",
    "summarize",
]

_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")

# prose is split into the forms that have to be told apart: a labelled item link, a shortcut item
# link, and a bare code span, which is never linked. the lookahead on the shortcut form keeps a
# reference-style link such as [`x`][ref] out of it.
_INLINE_CODE_RE = re.compile(
    r"(\[`+[^`]*`+\]\([^)\s]+\)"  # [`label`](path)
    r"|\[[^\[\]]+\]\([^)\s]+\)"  # [label](path)
    r"|\[`+[^`]*`+\](?![(\[])"  # [`path`]
    r"|`+[^`]*`+)"  # `code`
)
_ITEM_LINK_RE = re.compile(r"^\[`+\s*([^`]+?)\s*`+\]$")
_CODE_LABEL_RE = re.compile(r"^\[`+\s*([^`]+?)\s*`+\]\((\S+?)\)$")
_TEXT_LABEL_RE = re.compile(r"^\[([^\[\]]+)\]\((\S+?)\)$")

# a link target that is a URL rather than an item path: any scheme, or an absolute, anchored, or
# relative path. item paths are bare dotted identifiers, so they never look like these.
_URLISH_RE = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.-]*:|[/#]|\.{1,2}/)")


class CalloutType(StrEnum):
    """The kinds of callout Fumadocs knows how to render.

    Every admonition word a docstring can use maps onto one of these, since a type Fumadocs does
    not recognise renders as nothing at all.
    """

    INFO = "info"
    WARN = "warn"
    ERROR = "error"


_CALLOUT_TYPES = {
    "warning": CalloutType.WARN,
    "caution": CalloutType.WARN,
    "attention": CalloutType.WARN,
    "danger": CalloutType.ERROR,
    "error": CalloutType.ERROR,
}


def encode_text(
    text: str | None,
    links: LinkTable,
    scope: str | None = None,
    on_unresolved: Callable[[str], None] | None = None,
) -> str:
    """Escape the characters MDX would read as markup, and resolve the item links.

    Code is left exactly as written. MDX already treats `<` and `{` literally inside fenced,
    indented, and inline code, so escaping there would leak backslashes into the rendered code.

    Two link forms are recognised, as in rustdoc. The shortcut form shows the path as written; the
    labelled form shows the label instead, which is how a long path stays out of a sentence. A
    label that is not code renders as prose rather than monospace.

    A path is fully qualified (`example.Client.close`), partly qualified (`Client.close`), bare
    (`close`), or written against the page being rendered (`self`, `self.close`).

    Args:
        text: The docstring text, or `None`.
        links: Where names resolve to.
        scope: The page being rendered, for bare and `self` paths.
        on_unresolved: Called with the path when a shortcut link names nothing documented. A
            labelled link is never reported, since that syntax is also an ordinary markdown link.

    Returns:
        MDX ready to be written into a page.

    Examples:
        ```python
        encode_text("see [`Client.close`]", links)
        # 'see <PdxRef href="/api/example/Client#close">Client.close</PdxRef>'
        ```
    """

    if not text:
        return ""

    lines: list[str] = []
    in_fence = False
    for line in text.split("\n"):
        if in_fence:
            lines.append(line)
            if _FENCE_RE.match(line):
                in_fence = False

        elif _FENCE_RE.match(line):
            in_fence = True
            lines.append(line)

        elif line[:4] == "    ":
            lines.append(line)

        else:
            lines.append(_encode_line(line, links, scope, on_unresolved))

    return "\n".join(lines)


def summarize(text: str | None) -> str:
    """The first paragraph of a docstring, on one line.

    This is what a navigation card shows. Convention puts the summary first, so the first paragraph
    is the sentence its author already wrote for the purpose: nothing needs truncating, and nothing
    ends up cut off mid-word.

    Args:
        text: The docstring, or `None`.

    Returns:
        The first paragraph with its line breaks collapsed, or an empty string.
    """

    if not text:
        return ""

    paragraph = text.strip().split("\n\n", 1)[0]

    return " ".join(paragraph.split())


def jsx_props(**props: object) -> str:
    """Render keyword arguments as JSX attributes, as in `name={"close"}`.

    Values are JSON encoded, so the quotes and backslashes that turn up in signatures and defaults
    survive intact. A prop whose value is `None` is left off the element entirely, rather than
    passed as an explicit nothing.

    Args:
        **props: The attributes to render.

    Returns:
        The attributes separated by spaces, ready to go inside a tag.
    """

    parts = (f"{key}={{{json.dumps(value)}}}" for key, value in props.items() if value is not None)

    return " ".join(parts)


def callout_type(kind: str) -> CalloutType:
    """The callout an admonition of `kind` becomes.

    Args:
        kind: The admonition word, such as `warning`.

    Returns:
        The callout that word asks for, or [`CalloutType.INFO`] for a word carrying no urgency.
    """

    return _CALLOUT_TYPES.get(kind.lower(), CalloutType.INFO)


def fence(text: str | None) -> str:
    """A code fence long enough to hold `text` without `text` closing it early.

    Source and examples routinely contain fences of their own, and three backticks wrapped around
    three backticks end the block at the inner pair. That leaves the rest of the page as prose and
    the closing fence unmatched.

    Args:
        text: What the fence has to hold.

    Returns:
        A run of backticks, at least three long and always longer than the longest run inside.
    """

    longest = max((len(run) for run in re.findall(r"`+", text or "")), default=0)

    return "`" * max(3, longest + 1)


def escape_identifier(name: str) -> str:
    """Escape the underscores in `name`, so `__init__` is not read as emphasis in a heading.

    Args:
        name: The identifier to escape.

    Returns:
        The name with a backslash before each underscore.
    """

    return name.replace("_", "\\_")


def _encode_line(
    line: str, links: LinkTable, scope: str | None, on_unresolved: Callable[[str], None] | None
) -> str:
    parts: list[str] = []
    for part in _INLINE_CODE_RE.split(line):
        if part.startswith("["):
            parts.append(_resolve_link(part, links, scope, on_unresolved))

        elif part.startswith("`"):
            parts.append(part)  # a plain code span is never linked behind the author's back

        else:
            parts.append(_escape(part))

    return "".join(parts)


def _escape(text: str) -> str:
    return text.replace("<", "\\<").replace("{", "\\{").replace("}", "\\}")


def _resolve_link(
    span: str, links: LinkTable, scope: str | None, on_unresolved: Callable[[str], None] | None
) -> str:
    if match := _CODE_LABEL_RE.match(span):
        return _labelled(span, match.group(1), match.group(2), links, scope, code=True)

    if match := _TEXT_LABEL_RE.match(span):
        return _labelled(span, match.group(1), match.group(2), links, scope, code=False)

    match = _ITEM_LINK_RE.match(span)
    if not match:
        return _escape(span)

    path = match.group(1)
    href = links.resolve(path, scope)
    if not href:
        # a shortcut link names an item and nothing else, so a miss is a typo or a stale rename.
        # render it as code rather than as a link that scrolls nowhere, and say so.
        if on_unresolved is not None:
            on_unresolved(path)

        return f"`{path}`"

    return f'<PdxRef href="{href}">{expand_self(path, scope)}</PdxRef>'


def _labelled(
    span: str, label: str, target: str, links: LinkTable, scope: str | None, *, code: bool
) -> str:
    """`[label](path)` where the path names a documented item, else the link is left alone.

    Unlike the shortcut form, a miss here is not reported: the same syntax is an ordinary markdown
    link, and a relative link to a hand-written page is not a mistake.
    """

    if _URLISH_RE.match(target) or not (href := links.resolve(target, scope)):
        return _escape(span)

    # a code label is an identifier and keeps its monospace; a prose label reads as prose
    if code:
        return f'<PdxRef href="{href}" title="{expand_self(target, scope)}">{label}</PdxRef>'

    return f"[{label}]({href})"
