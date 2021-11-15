#!/usr/bin/env python
import re
import logging
import panflute as pf
from latex_to_myst.helpers import get_element_type, is_directive_block, directive_level
from latex_to_myst.figures import action as figure_action
from latex_to_myst.math import action as math_action
from latex_to_myst.hyperlink import action as link_action
from latex_to_myst.basic import action as basic_action

logger = logging.getLogger(__name__)
ACTIONS = (
    ("Math", math_action),
    ("Link", link_action),
    ("Figure", figure_action),
    ("Basic", basic_action),
)


def finalize(doc: pf.Doc):
    # add in title labels
    for n, (elem, label) in enumerate(doc.section_labels_to_insert.items()):
        idx = doc.content.index(elem)
        doc.content.insert(idx, pf.RawBlock(f"({label.strip()})=", format="markdown"))


def prepare(doc: pf.Doc):
    # determine level of blocks
    block_levels = {}

    def get_level(e, d):
        if is_directive_block(e):
            level = directive_level(e, doc)
            block_levels[e] = level

    doc.walk(get_level)
    doc.element_levels = block_levels

    # determine labels of blocks for hyperlinks
    block_labels = {}

    def gather_labels(e, doc):
        if hasattr(e, "identifier"):
            if e.identifier:
                block_labels[e.identifier] = e
        elif get_element_type(e) == "displaymath":
            label = "eqn"
            if "\label" in pf.stringify(e):
                label = re.findall(r"\\label\{([^\}]+)\}", e.text)[0]
            block_labels[label] = e

    doc.walk(gather_labels)
    doc.element_labels = block_labels

    doc.section_labels_to_insert = {}


def main(doc: pf.Doc = None):
    return pf.run_filters(
        [math_action, link_action, figure_action, basic_action],
        doc=doc,
        finalize=finalize,
        prepare=prepare,
    )


if __name__ == "__main__":
    main()
