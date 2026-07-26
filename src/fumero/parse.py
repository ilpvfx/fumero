"""Read a Python module with griffe and describe it in [`fumero.model`] terms.

This is the only part of fumero that knows griffe exists. Everything downstream works from the
model, so a change in how a module is introspected never reaches the output.

Start at [`load_module`], which reads a module and hands back the tree the rest of this module
takes apart.
"""

import re
from typing import cast

import griffe

from .config import Config
from .error import ModuleNotFound
from .model import Admonition, ParsedDocstring, Property

__all__ = [
    "load_module",
    "module_attributes",
    "parse_docstring",
    "parse_function_definition",
    "public_members",
    "remove_prefix",
]

_MODULE_PREFIX_RE = re.compile(r"(?:[a-z_][a-z0-9_]*\.)+([A-Z][A-Za-z0-9_]*)")


def load_module(name: str, config: Config | None = None) -> griffe.Module:
    """Read a module and hand back griffe's view of it.

    A package is a module that happens to hold other modules, so either will do: `example` reads
    the whole package, `example.core` reads that subtree on its own.

    Args:
        name: An importable module path.
        config: Supplies the docstring dialect. Defaults are used when this is `None`.

    Returns:
        The module, and everything under it.

    Raises:
        ModuleNotFound: `name` is not importable from here.

    Examples:
        ```python
        module = load_module("example")
        ```
    """

    config = config or Config()
    try:
        loaded = griffe.load(name, docstring_parser=griffe.Parser(config.dialect))
    except ImportError as error:
        raise ModuleNotFound(name) from error

    return cast(griffe.Module, loaded)


def public_members(
    module: griffe.Module, kind: griffe.Kind, config: Config
) -> list[griffe.Object | griffe.Alias]:
    """The members of `module` of one kind that belong in the documentation.

    `__all__` decides what is public. A module that defines one is taken at its word; a module that
    does not falls back to the convention that a leading underscore means private.

    Args:
        module: The module to look through.
        kind: The kind of member to collect, such as `griffe.Kind.CLASS`.
        config: Supplies the exclude patterns.

    Returns:
        The matching members, in the order the module declares them.
    """

    exports = None if module.exports is None else {str(export) for export in module.exports}

    def is_public(name: str, member: griffe.Object | griffe.Alias) -> bool:
        exported = not name.startswith("_") if exports is None else name in exports

        return exported and not config.excludes(member)

    return [
        member
        for name, member in module.members.items()
        if member.kind is kind and is_public(name, member)
    ]


def module_attributes(module: griffe.Module, config: Config) -> list[Property]:
    """The module's public attributes, sorted by name.

    Type aliases are attributes as far as griffe is concerned, which is what lets a signature link
    to one.

    Args:
        module: The module to look through.
        config: Supplies the exclude patterns.

    Returns:
        One [`fumero.model.Property`] per attribute.
    """

    attributes = [
        _attribute_property(attribute)
        for attribute in module.attributes.values()
        if not attribute.name.startswith("_") and not config.excludes(attribute)
    ]

    return sorted(attributes, key=lambda attribute: attribute.name)


def parse_docstring(parent: griffe.Alias | griffe.Class | griffe.Function) -> ParsedDocstring:
    """Split a docstring into the sections a page renders separately.

    The signature is read first, so every parameter and the return type are described whether the
    docstring mentions them or not. An `Args:` entry then fills in the prose for the parameter it
    names, which is why the parameter list stays in signature order rather than docstring order.

    Args:
        parent: The class or function to read.

    Returns:
        The sections of the docstring. A `parent` with no docstring at all still yields its
        parameters and return type, since those come from the signature.
    """

    parameters = [_parameter_property(parameter) for parameter in _callable_parameters(parent)]
    attributes = [
        _attribute_property(attribute)
        for attribute in parent.attributes.values()
        if not attribute.name.startswith("_")
    ]
    returns = _return_property(parent)

    if not parent.docstring:
        return ParsedDocstring(parameters=parameters, returns=returns)

    description: str | None = None
    raises: list[Property] = []
    admonitions: list[Admonition] = []

    for index, section in enumerate(parent.docstring.parsed):
        match section:
            case griffe.DocstringSectionText() if index == 0:
                description = section.value

            case griffe.DocstringSectionParameters():
                parameters = _described_parameters(parent, section.value)

            case griffe.DocstringSectionAttributes():
                attributes = _described_attributes(parent, section.value)

            case griffe.DocstringSectionReturns() | griffe.DocstringSectionYields():
                if returns is not None and section.value:
                    returns.description = section.value[0].description or None

            case griffe.DocstringSectionRaises():
                raises = [_raise_property(raised) for raised in section.value]

            case griffe.DocstringSectionAdmonition():
                admonitions.append(_admonition(section))

            case griffe.DocstringSectionExamples():
                admonitions.extend(_examples(section))

    return ParsedDocstring(description, parameters, attributes, raises, admonitions, returns)


def _described_parameters(
    parent: griffe.Alias | griffe.Class | griffe.Function,
    documented: list[griffe.DocstringParameter],
) -> list[Property]:
    """The signature's parameters, each carrying the prose its `Args:` entry gave it."""

    descriptions = {entry.name: entry.description for entry in documented}

    return [
        _parameter_property(parameter, descriptions.get(parameter.name))
        for parameter in _callable_parameters(parent)
    ]


def _described_attributes(
    parent: griffe.Alias | griffe.Class | griffe.Function,
    documented: list[griffe.DocstringAttribute],
) -> list[Property]:
    """The attributes as declared, each carrying the prose its `Attributes:` entry gave it."""

    descriptions = {entry.name: entry.description for entry in documented}

    return [
        _attribute_property(attribute, descriptions.get(attribute.name))
        for attribute in parent.attributes.values()
        if not attribute.name.startswith("_")
    ]


def _return_property(parent: griffe.Alias | griffe.Class | griffe.Function) -> Property | None:
    """The return value read from the signature, before a `Returns:` section describes it."""

    if parent.kind is not griffe.Kind.FUNCTION:
        return None

    if not isinstance(parent, griffe.Alias | griffe.Function):
        return None

    annotation = remove_prefix(str(parent.returns)) if parent.returns is not None else None

    return Property(parent.name, annotation, None, None)


def _raise_property(documented: griffe.DocstringRaise) -> Property:
    """One `Raises:` entry, named after the exception it records."""

    annotation = (
        remove_prefix(str(documented.annotation)) if documented.annotation is not None else None
    )

    return Property(annotation or "", annotation, documented.description or None, None)


def _admonition(section: griffe.DocstringSectionAdmonition) -> Admonition:
    kind = str(section.value.kind)

    return Admonition(kind, section.title or kind.title(), section.value.contents)


def _examples(section: griffe.DocstringSectionExamples) -> list[Admonition]:
    """An `Examples:` section, split into the prose and the doctests it alternates between.

    Prose arrives as markdown and passes through as written; a doctest arrives as bare source and
    needs a fence put round it, which the template does once it knows which is which.
    """

    return [
        Admonition(
            "example" if kind is griffe.DocstringSectionKind.examples else "markdown",
            section.title or "Example",
            content,
        )
        for kind, content in section.value
    ]


def _parameter_property(parameter: griffe.Parameter, description: str | None = None) -> Property:
    annotation = (
        remove_prefix(str(parameter.annotation)) if parameter.annotation is not None else None
    )
    value = str(parameter.default) if parameter.default is not None else None

    return Property(parameter.name, annotation, description, value)


def parse_function_definition(function: griffe.Function, width: int = 84) -> str:
    """The `def` line as documentation shows it, rather than as the interpreter sees it.

    A leading `self` or `cls` is dropped, because it is not something a caller passes, and there is
    no trailing colon, because this is a thing to read rather than a line to run.

    A definition too long for `width` breaks one parameter to a line. That is the only reason a
    long signature can be shown at all: on one line a fifteen-parameter constructor is a horizontal
    scrollbar, and the same thing wrapped is a list you can read down.

    Args:
        function: The function to describe.
        width: The column to break the line at.

    Returns:
        A definition, on one line where it fits and on several where it does not.

    Examples:
        ```python
        parse_function_definition(function)
        # 'def connect(host: str, port: int = 8080) -> None'
        ```
    """

    parts = _parameter_parts(function)
    returns = f" -> {remove_prefix(str(function.annotation))}" if function.annotation else ""
    head = f"def {function.name}("

    one_line = f"{head}{', '.join(parts)}){returns}"
    if len(one_line) <= width:
        return one_line

    # black's shape: one parameter to a line, a trailing comma, and the closing parenthesis
    # carrying the return type
    body = "".join(f"    {part},\n" for part in parts)

    return f"{head}\n{body}){returns}"


def _parameter_parts(function: griffe.Function) -> list[str]:
    """Each parameter as a definition writes it, with the markers that separate the kinds."""

    parts: list[str] = []
    parameters = _callable_parameters(function)

    has_positional_only = any(
        parameter.kind is griffe.ParameterKind.positional_only for parameter in parameters
    )
    positional_only_closed = False
    keyword_only_opened = False

    for parameter in parameters:
        if (
            has_positional_only
            and not positional_only_closed
            and parameter.kind is not griffe.ParameterKind.positional_only
        ):
            parts.append("/")
            positional_only_closed = True

        if parameter.kind is griffe.ParameterKind.keyword_only and not keyword_only_opened:
            parts.append("*")
            keyword_only_opened = True

        match parameter.kind:
            case griffe.ParameterKind.var_positional:
                part = f"*{parameter.name}"
                keyword_only_opened = True

            case griffe.ParameterKind.var_keyword:
                part = f"**{parameter.name}"

            case _:
                part = parameter.name

        if parameter.annotation is not None:
            part += f": {remove_prefix(str(parameter.annotation))}"
            separator = " = "

        else:
            separator = "="

        variadic = {griffe.ParameterKind.var_positional, griffe.ParameterKind.var_keyword}
        if parameter.default is not None and parameter.kind not in variadic:
            part += f"{separator}{parameter.default}"

        parts.append(part)

    if has_positional_only and not positional_only_closed:
        parts.append("/")

    return parts


def _callable_parameters(
    parent: griffe.Alias | griffe.Class | griffe.Function,
) -> list[griffe.Parameter]:
    """The parameters a caller passes, without the receiver a bound method is called through."""

    parameters = list(parent.parameters)
    if parameters and parameters[0].name in {"self", "cls"}:
        return parameters[1:]

    return parameters


def _attribute_property(attribute: griffe.Attribute, description: str | None = None) -> Property:
    annotation = (
        remove_prefix(str(attribute.annotation)) if attribute.annotation is not None else None
    )
    value = str(attribute.value) if attribute.value is not None else None

    return Property(attribute.name, annotation, description, value)


def remove_prefix(text: str) -> str:
    """Strip the module paths from type references, so `pathlib.Path` reads as `Path`.

    Relies on the convention that class names are CapitalCase. A dotted name ending in a lowercase
    word is left alone, since it is far more likely to name a value than a type.

    Args:
        text: A type annotation as written.

    Returns:
        The annotation with each type named on its own.

    Examples:
        ```python
        remove_prefix("dict[str, pathlib.Path]")
        # 'dict[str, Path]'
        ```
    """

    return _MODULE_PREFIX_RE.sub(r"\1", text.replace("builtins.", ""))
