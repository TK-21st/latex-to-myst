#!/usr/bin/env python
"""Main entry point to document parser
"""
import re
import logging
import panflute as pf
from .helpers import (
    get_element_type,
    TERMINAL_SIZE,
)
from .directives import is_directive_block, directive_level
from .figures import action as figure_action
from .math import action as math_action
from .hyperlink import action as link_action
from .basic import action as basic_action

logger = logging.getLogger(__name__)

# The following conversion actions are run upon processing a given
# .tex file, and are executed _in this sequence_
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
    logger.info("Preparing document for processing...")

    # determine level of blocks
    logger.info("Parsing nested levels of directive blocks.")
    doc.element_levels = {}

    def get_level(e, doc):
        if is_directive_block(e):
            level = directive_level(e, doc)
            doc.element_levels[e] = level

    doc.walk(get_level)

    # determine labels of blocks for hyperlinks
    logger.info("Parsing labels for directive blocks.")
    doc.element_labels = {}

    def gather_labels(e, doc):
        if get_element_type(e) == "displaymath":
            label_in_text = re.search(r"\\label\{([^\}]*)\}", e.text)
            if label_in_text:
                (label,) = label_in_text.groups()
                doc.element_labels[label] = e

        if hasattr(e, "identifier"):
            if e.identifier:
                doc.element_labels[e.identifier] = e

    doc.walk(gather_labels)
    logger.debug(f"Discovered Labels: {list(doc.element_labels.keys())}")

    doc.section_labels_to_insert = {}


def main(doc: pf.Doc = None):
    return pf.run_filters(
        [act for _, act in ACTIONS],
        doc=doc,
        finalize=finalize,
        prepare=prepare,
    )


if __name__ == "__main__":
    main()
