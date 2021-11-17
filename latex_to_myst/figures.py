"""Figures directives
"""
import re
import logging
import typing as tp
import panflute as pf
from latex_to_myst.helpers import create_directive_block, elem_has_multiple_figures

logger = logging.getLogger(__name__)


def image_in_subplot(elem: pf.Image):
    """Check if an image node is in subplot"""
    if isinstance(elem.parent, pf.Para):
        return elem_has_multiple_figures(elem.parent)
    if isinstance(elem.ancestor(1), pf.TableCell):
        table = elem.ancestor(4)
        return elem_has_multiple_figures(table)
    if isinstance(elem.ancestor(2), pf.TableCell):
        table = elem.ancestor(5)
        return elem_has_multiple_figures(table)
    return False


def break_long_string(string: str, max_len: int = 70, indent: int = 0) -> str:
    """Break long string into shorter strings of max_len (with indent added)"""
    import numpy as np

    string = " ".join(
        string.split(" ")
    )  # convert multiple consecutive white spaces to single
    content = string.split(" ")
    str_len = [len(c) + 1 for c in content]  # +1 for whitespace
    cum_len = np.cumsum(str_len)
    block_idx = np.floor(cum_len / max_len).astype(int)
    N_blocks = max(block_idx) + 1
    content = np.array(content, dtype=str)
    output = ""
    for b in range(N_blocks):
        (idx,) = np.where(block_idx == b)
        new_line = " " * indent + " ".join(content[idx].tolist()) + "\n"
        output += new_line
    output.rstrip("\n")  # remove last newline
    return output


def create_image(elem: pf.Image, doc: pf.Doc = None) -> pf.Span:
    """Create Image Directive Block"""
    if not isinstance(elem, pf.Image):
        return
    url = elem.url
    for name, val in elem.attributes.items():
        if name in ["width", "height"]:
            # replace width with ratio
            _match = re.search(
                r"([0-9|.]*)((?:\\textheight|\\lineheight|\\textwidth|\\linewidth))",
                val,
            )
            if _match:
                _scale, _ = _match.groups()
                if _scale:
                    val = f"{float(_scale)*100:.0f}%"
                else:
                    val = "100%"
                elem.attributes[name] = val

    return create_directive_block(elem, doc, elem.content, "figure", pf.Span, label=url)


def _gather_subplot_identifiers(elem: tp.Union[pf.Para, pf.Table], doc: pf.Doc):
    """Gather all identifiers for superplot and subplots

    For subplots, the label of the overall figure could be lost and propagated
    to individual subfigures. Here, we check if that's the case, and assign
    individual identifiers for each figure if that's the case.
    """
    if hasattr(elem, "identifier") and elem.identifier:
        superfigure_identifier = elem.identifier
    else:
        superfigure_identifier = None
    subfigure_identifiers = {}

    def gather_identifier(e, doc):
        nonlocal subfigure_identifiers
        if isinstance(e, pf.Image):
            if hasattr(e, "identifier") and e.identifier:
                subfigure_identifiers[e] = e.identifier

    elem.walk(gather_identifier)

    if len(set(subfigure_identifiers.values())) == 1 and superfigure_identifier is None:
        # the superfigure identifier propgated to subfigures
        superfigure_identifier = list(subfigure_identifiers.values())[0]
        for n, e in enumerate(subfigure_identifiers.keys()):
            e.identifier = f"{superfigure_identifier}-{n}"
    elif (
        len(set(subfigure_identifiers.values())) == 0
        and superfigure_identifier is not None
    ):
        # the superfigure identifier is specified and subfigures have no identifier
        #  use superfigure identifier + index for reference identifier of each figure
        for n, e in enumerate(subfigure_identifiers.keys()):
            e.identifier = f"{superfigure_identifier}-{n}"
    elif (
        len(set(subfigure_identifiers.values())) == 0 and superfigure_identifier is None
    ):
        ctr = 0
        superfigure_identifier = f"subplots-{ctr}"
        while superfigure_identifier in doc.element_labels:
            ctr = 0
            superfigure_identifier = f"subplots-{ctr}"
    else:
        # do nothing
        pass
    elem.identifier = superfigure_identifier
    return elem


def _create_subplots_from_para(elem: pf.Para, doc: pf.Doc):
    """Create Subplot using list-table and return table and substitutions to put in header"""
    elem = _gather_subplot_identifiers(elem, doc)
    image_content = []
    images = {}
    start_new_row = True
    for n, e in enumerate(elem.content):
        if isinstance(e, pf.LineBreak):
            start_new_row = True
        if isinstance(e, pf.Image):
            image_id = f"figure-{len(doc.metadata['substitutions'].content)}"
            if e.identifier:
                image_id += f":{e.identifier}"
            if image_id in doc.metadata["substitutions"].content:
                logger.error(f"Image ID {image_id} already exists, skipping.")
                continue
            # store img in images for substitutions
            images[image_id] = create_image(e, doc)
            if start_new_row:
                image_content.append(
                    pf.RawInline("* - {{ %s }}\n" % image_id, format="markdown")
                )
                start_new_row = False
            else:
                image_content.append(
                    pf.RawInline("  - {{ %s }}\n" % image_id, format="markdown")
                )
    return image_content, images


def _create_subplots_from_table(elem: pf.Table, doc: pf.Doc):
    """Create Subplot using list-table and return table and substitutions to put in header"""
    elem = _gather_subplot_identifiers(elem, doc)

    start_new_row = True
    image_content = []
    images = {}

    def walk_table_of_figures(e, doc):
        nonlocal start_new_row
        nonlocal image_content
        if isinstance(e, pf.TableRow):
            start_new_row = True
            return
        if isinstance(e, pf.Image):
            image_id = f"figure-{len(doc.metadata['substitutions'].content)}"
            if e.identifier:
                image_id += f":{e.identifier}"
            assert image_id not in doc.metadata["substitutions"].content
            images[image_id] = create_image(e, doc)
            if start_new_row:
                image_content.append(
                    pf.RawInline("* - {{%s}}\n" % image_id, format="markdown")
                )
                start_new_row = False
            else:
                image_content.append(
                    pf.RawInline("  - {{%s}}\n" % image_id, format="markdown")
                )
        return

    elem.walk(walk_table_of_figures)
    return image_content, images


def create_subplots(
    elem: tp.Union[pf.Para, pf.Table], doc: pf.Doc = None
) -> tp.Tuple[pf.Para, tp.Iterable[tp.Any]]:
    """Create Subplot using list-table and return table and substitutions to put in header"""
    if not "substitutions" in doc.metadata:
        doc.metadata["substitutions"] = {}

    if isinstance(elem, pf.Para):
        image_content, sub_images = _create_subplots_from_para(elem, doc)
    elif isinstance(elem, pf.Table):
        image_content, sub_images = _create_subplots_from_table(elem, doc)
    else:
        raise TypeError(
            f"Element of type {type(elem)} not supported, need to be Para or Table."
        )

    # store subfigures in metadata
    for image_id, img in sub_images.items():
        while pf.stringify(img).startswith("\n"):
            img.content = img.content[1:]
        while pf.stringify(img).startswith("\r"):
            img.content = img.content[1:]
        doc.metadata["substitutions"].content[image_id] = pf.MetaInlines(img)

    # get caption of overall figure
    caption = pf.stringify(elem)
    return create_directive_block(
        elem, doc, image_content, "list-table", pf.Para, label=caption
    )


def action(elem: pf.Element, doc: pf.Doc = None):
    """Figure Actions"""
    if isinstance(elem, pf.Para):
        if elem_has_multiple_figures(elem):
            logger.debug("Creating subfigure from Para.")
            logger.debug(elem)
            logger.debug(pf.stringify(elem))
            return create_subplots(elem, doc)
        return elem

    if isinstance(elem, pf.Table):
        if elem_has_multiple_figures(elem):
            logger.debug("Creating subfigure from Table.")
            logger.debug(elem)
            logger.debug(pf.stringify(elem))
            return create_subplots(elem, doc)
        return elem

    if isinstance(elem, pf.Image):
        if image_in_subplot(elem):
            return elem
        logger.debug(f"Creating Figure: {elem.url}")
        return create_image(elem, doc)


def main(doc: pf.Doc):
    return pf.run_filter(action, doc=doc)


if __name__ == "__main__":
    main()
