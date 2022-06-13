"""Basic Pandoc Filters
"""
import logging
import panflute as pf
from .directives import create_directive_block, create_generic_div_block

logger = logging.getLogger(__name__)


def is_isolated_label(elem, doc=None) -> str:
    """check if element is isolated label

    Returns the label if is isolated label, else return False
    """
    if not elem:
        return False
    if len(elem.content) == 1:
        if isinstance(elem.content[0], pf.Span):
            if "label" in elem.content[0].attributes:
                label = elem.content[0].attributes["label"]
                if pf.stringify(elem).strip(" \n\r") == f"[{label}]":
                    return label
    return False


def action(elem: pf.Element, doc: pf.Doc = None) -> pf.Element:
    """Set of Basic Filters"""
    if isinstance(elem, pf.Para) and is_isolated_label(elem):
        return []

    if isinstance(elem, pf.Str):
        # remove section and figure before references.
        if isinstance(elem.next, pf.Link) or (
            elem.next is not None and isinstance(elem.next.next, pf.Link)
        ):
            if elem.text.lower() in ["section", "figure", "fig"]:
                return []
        return elem

    if isinstance(elem, pf.Header):
        if is_isolated_label(elem.next):
            logger.debug("Header is followed by isolated header on next line.")
            label = is_isolated_label(elem.next)
        else:
            label = elem.identifier

        # store the section header to insert as doc attribute to be inserted
        # at the end
        if not hasattr(doc, "section_labels_to_insert"):
            doc.section_labels_to_insert = {}
        doc.section_labels_to_insert[elem] = label
        elem.identifier = ""
        elem.classes = []
        return elem

    if isinstance(elem, pf.CodeBlock):
        elem.attributes = {}
        return elem

    if isinstance(elem, pf.Div):
        return create_generic_div_block(elem, doc)


def main(doc: pf.Doc):
    return pf.run_filter(action, doc=doc)


if __name__ == "__main__":
    main()
