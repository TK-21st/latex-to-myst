#!/usr/bin/env python
import re
import logging
import panflute as pf
from latex_to_myst.helpers import (
    get_element_type,
    is_directive_block,
    directive_level,
    TERMINAL_SIZE,
)
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
    logger.debug("Discovered Labels")
    logger.debug("-" * (TERMINAL_SIZE.columns - 8))  # subtract 8 for  "[DEBUG] "
    logger.debug(list(doc.element_labels.keys()))
    logger.debug("-" * (TERMINAL_SIZE.columns - 8))  # subtract 8 for  "[DEBUG] "

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
