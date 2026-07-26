"""The shape of a documented API, independent of how it is rendered.

These are plain dataclasses holding plain strings. No griffe types reach them, so a template can
read a documented module without knowing how that module was introspected, and a caller who wants
only the structure of a package can take it without rendering anything.

Start at [`Module`], which is what one page of the reference is built from.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["Admonition", "Card", "Class", "Function", "Module", "ParsedDocstring", "Property"]


@dataclass
class Admonition:
    """A block lifted out of a docstring to be rendered apart from the prose around it.

    Attributes:
        kind: `example` for a code block, `markdown` for prose that passes through as written, or
            an admonition word such as `warning`, which becomes a callout.
        title: The heading the block is rendered under.
        content: The body, still in markdown.
    """

    kind: str
    title: str
    content: str


@dataclass
class Card:
    """A navigation entry for something documented on a page of its own.

    Carries the target's docstring as well as its name, because a list of bare names makes a reader
    open every page to find the one they wanted.

    Attributes:
        name: The short name, used as the card's title and in its link.
        docstring: The target's docstring, summarised to its first paragraph when rendered.
    """

    name: str
    docstring: str | None = None


@dataclass
class Class:
    """A class and everything documented on its page.

    Attributes:
        name: The short name.
        docstring: The parsed docstring.
        constructor: `__init__` or `__new__` as a [`Function`], or `None` for a class defining
            neither. A constructor is a method, so it is documented as one rather than as a second
            kind of thing with a signature of its own.
        attributes: Public class attributes.
        functions: Public methods, sorted by name.
        classes: Nested classes, each of which gets a page of its own.
    """

    name: str
    docstring: ParsedDocstring
    constructor: Function | None = None
    attributes: list[Property] = field(default_factory=list)
    functions: list[Function] = field(default_factory=list)
    classes: list[Class] = field(default_factory=list)


@dataclass
class Function:
    """A function or a method, which are documented the same way.

    Attributes:
        name: The short name, not the dotted path.
        docstring: The parsed docstring.
        definition: The `def` line as documentation shows it: without the receiver, and wrapped one
            parameter to a line when it is too long to read across.
        source: The function's source text, empty when it could not be read.
    """

    name: str
    docstring: ParsedDocstring
    definition: str
    source: str = ""


@dataclass
class Module:
    """A module and the members documented on its page.

    Attributes:
        name: The short name, not the dotted path.
        docstring: The module docstring, unparsed. A module page renders it as prose rather than
            splitting it into sections the way a function page does.
        attributes: Module-level attributes, including type aliases.
        classes: Classes documented under this module, each on a page of its own.
        functions: Module-level functions.
        modules: Child modules as navigation cards rather than whole modules, because each one is
            rendered by a pass of its own instead of nested inside this one.
    """

    name: str
    docstring: str | None
    attributes: list[Property] = field(default_factory=list)
    classes: list[Class] = field(default_factory=list)
    functions: list[Function] = field(default_factory=list)
    modules: list[Card] = field(default_factory=list)


@dataclass
class ParsedDocstring:
    """A docstring split into the sections a page renders separately.

    Every field has an empty default, so an undocumented function still holds one of these rather
    than nothing at all.

    Attributes:
        description: The leading prose, before any section.
        parameters: Documented parameters, in signature order.
        attributes: Documented attributes.
        raises: Exceptions the docstring records, each with the type raised and the reason.
        admonitions: Examples and callouts, in the order they were written.
        returns: The return value, or `None` for something that returns nothing.
    """

    description: str | None = None
    parameters: list[Property] = field(default_factory=list)
    attributes: list[Property] = field(default_factory=list)
    raises: list[Property] = field(default_factory=list)
    admonitions: list[Admonition] = field(default_factory=list)
    returns: Property | None = None


@dataclass
class Property:
    """A named, typed thing: a parameter, an attribute, or a return value.

    All three read the same way on a page, so they share one shape rather than three that differ
    only in which fields happen to be filled in.

    Attributes:
        name: The name as written in the source.
        annotation: The type annotation, or `None` when the item carries none.
        description: Prose from the docstring, or `None` when the item is undocumented.
        value: The default or assigned value as source text, or `None`.
    """

    name: str
    annotation: str | None
    description: str | None
    value: str | None
