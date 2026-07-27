import re
from pathlib import Path

import pytest

import fumero
from fumero.render import Result


@pytest.fixture
def reference(tmp_path: Path) -> Result:
    return fumero.generate("fumero", fumero.Config(output=tmp_path, base_url="/docs/api"))


def test_fumero_documents_itself_with_no_broken_links(reference: Result):
    assert [str(link) for link in reference.unresolved] == []
    assert reference.ok


def test_every_generated_page_gives_each_anchor_to_one_thing(reference: Result):
    for page in reference.pages:
        anchors = re.findall(r"\[#([^\]]+)\]", page.read_text())

        assert len(anchors) == len(set(anchors)), f"duplicate anchor in {page.name}"


def test_every_exported_name_reaches_a_page():
    config = fumero.Config(base_url="/docs/api")
    table = fumero.LinkTable.collect(fumero.load_module("fumero", config), config)

    assert [name for name in fumero.__all__ if table.resolve(name) is None] == []


def test_the_model_keeps_a_namespace_of_its_own():
    assert [name for name in fumero.model.__all__ if hasattr(fumero, name)] == []
