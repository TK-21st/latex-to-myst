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
    label = elem.identifier
    attr = elem.attributes
    attr_str = ""
    for name, val in attr.items():
        if name == "height":
            continue
        _match = re.findall(r"([0-9|.]*)(\\textwidth)", val)
        if _match:
            if _match[0][0]:
                val = f"{str(int(float(_match[0][0])*100))}%"
            else:
                val = "100%"
        _match = re.findall(r"([0-9|.]*)(\\linewidth)", val)
        if _match:
            if _match[0][0]:
                val = f"{str(int(float(_match[0][0])*100))}%"
            else:
                val = "100%"
        attr_str += f":{name}: {val}\n"

    if pf.stringify(elem) == "image":  # remove default caption
        caption = []
    else:
        caption = elem.content

    content = []
    if label:
        content.append(pf.RawInline(f":name: {label}\n", format="markdown"))
    if attr_str:
        content.append(pf.RawInline(f"{attr_str}", format="markdown"))
    content += caption
    return create_directive_block(elem, doc, content, "figure", pf.Span, label=url)


def _create_subplots_from_para(elem: pf.Para, doc):
    """Create Subplot using list-table and return table and substitutions to put in header"""
    image_ids = []
    image_content = []
    start_new_row = True
    for n, e in enumerate(elem.content):
        if isinstance(e, pf.LineBreak):
            start_new_row = True
        if isinstance(e, pf.Image):
            image_id = f"figure{len(doc.metadata['substitutions'].content)}"
            if e.identifier:
                image_id += f":{e.identifier}"
            image_ids.append(image_id)
            if image_id in doc.metadata["substitutions"].content:
                logger.error(f"Image ID {image_id} already exists, skipping.")
                continue
            img = create_image(e, doc)
            doc.metadata["substitutions"].content[image_id] = pf.MetaInlines(img)
            if start_new_row:
                image_content.append(
                    pf.RawInline("* - {{%s}}\n" % image_id, format="markdown")
                )
                start_new_row = False
            else:
                image_content.append(
                    pf.RawInline("  - {{%s}}\n" % image_id, format="markdown")
                )
    return image_content


def _create_subplots_from_table(elem: pf.Table, doc):
    """Create Subplot using list-table and return table and substitutions to put in header"""
    start_new_row = True
    image_content = []

    def walk_table_of_figures(e, doc):
        nonlocal start_new_row
        nonlocal image_content
        if isinstance(e, pf.TableRow):
            start_new_row = True
            return
        if isinstance(e, pf.Image):
            image_id = f"figure{len(doc.metadata['substitutions'].content)}"
            if e.identifier:
                image_id += f":{e.identifier}"
            assert image_id not in doc.metadata["substitutions"].content
            img = create_image(e, doc)
            doc.metadata["substitutions"].content[image_id] = pf.MetaInlines(img)
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
    return image_content


def create_subplots(
    elem: tp.Union[pf.Para, pf.Table], doc: pf.Doc = None
) -> tp.Tuple[pf.Para, tp.Iterable[tp.Any]]:
    """Create Subplot using list-table and return table and substitutions to put in header"""
    if not "substitutions" in doc.metadata:
        doc.metadata["substitutions"] = {}

    if isinstance(elem, pf.Para):
        image_content = _create_subplots_from_para(elem, doc)
    elif isinstance(elem, pf.Table):
        image_content = _create_subplots_from_table(elem, doc)
    else:
        raise TypeError(
            f"Element of type {type(elem)} not supported, need to be Para or Table."
        )

    label = None
    if hasattr(elem, "identifier"):
        label = elem.identifier

    caption = ""
    if hasattr(elem, "title"):
        caption = elem.title

    content = [
        pf.RawInline(f"\n:label: {label}" if label else "\n", format="markdown"),
        *image_content,
    ]
    return create_directive_block(
        elem, doc, content, "list-table", pf.Para, label=caption
    )


def action(elem: pf.Element, doc: pf.Doc = None):
    """Figure Actions"""
    if isinstance(elem, pf.Para):
        if elem_has_multiple_figures(elem):
            logger.debug("Creating subfigure from Para.")
            return create_subplots(elem, doc)
        return elem

    if isinstance(elem, pf.Table):
        if elem_has_multiple_figures(elem):
            logger.debug("Creating subfigure from Table.")
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
