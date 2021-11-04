#!/usr/bin/env python
import re
import panflute as pf
from panflute.elements import Doc
from latex_to_myst.latex_math import *
from latex_to_myst.figures import *
from latex_to_myst.declarative import *

section_labels_to_insert = {}

def get_element_type(elem: pf.Element):
    if isinstance(elem, pf.Image):
        return "figure"
    if isinstance(elem, pf.Para):
        if elem_has_multiple_figures(elem):
            return "subfigures"
    if isinstance(elem, pf.Math):
        if elem.format == 'DisplayMath':
            return "displaymath"
    if isinstance(elem, pf.Div):
        if elem.classes:
            if any([k in SUPPORTED_AMSTHM_BLOCKS for k in elem.classes]):
                return "amsthm"
    if isinstance(elem, pf.Header):
        return "header"
    return None

def is_isolated_label(elem, doc=None):
    """check if element is isolated label"""
    if not elem:
        return False
    if len(elem.content) == 1:
        if isinstance(elem.content[0], pf.Span):
            if 'label' in elem.content[0].attributes:
                label = elem.content[0].attributes['label']
                if pf.stringify(elem).strip(' \n\r') == f"[{label}]":
                    return label
    return False

def action(elem: pf.Element, doc: pf.Doc = None) -> pf.Element:
    if isinstance(elem, pf.Para) and is_isolated_label(elem):
        return []

    if isinstance(elem, pf.Doc):
        return elem
    if isinstance(elem, pf.Str):
        # remove section and figure before references.
        if isinstance(elem.next, pf.Link) or (
            elem.next is not None and
            isinstance(elem.next.next, pf.Link)
        ):
            if elem.text.lower() in ['section', 'figure', 'fig']:
                return []
        return elem

    if isinstance(elem, pf.Header):
        if is_isolated_label(elem.next):
            label = is_isolated_label(elem.next)
        else:
            label = elem.identifier
        section_labels_to_insert[elem] = label
        elem.identifier = ""
        elem.classes = []
        return elem

    if isinstance(elem, pf.Para):
        if elem_has_multiple_figures(elem):
            return create_subplots(elem, doc)
        return elem

    if isinstance(elem, pf.Table):
        if elem_has_multiple_figures(elem):
            return create_subplots(elem, doc)
        return elem

    if isinstance(elem, pf.Image):
        if image_in_subplot(elem):
            return elem
        return create_image(elem, doc)

    if isinstance(elem, pf.Link):

        if not elem.attributes:
            if 'http' in elem.url:
                elem.url = ''.join(elem.url.split(' '))
            return elem

        if hasattr(elem, 'attributes') and 'reference' in elem.attributes:
            target = str(elem.attributes['reference'])
            reftype= elem.attributes['reference-type']
            elem.attributes = {}
            elem.url = target

            if target in doc.element_labels:
                target_elem = doc.element_labels[target]
                target_type = get_element_type(target_elem)
                if not target_type:
                    return elem
                else:
                    if target_type in ['figure']:
                        return pf.RawInline("{numref}`%s`" % target, format='markdown')
                    elif target_type in ['subfigures', 'dislaymath', 'header']:
                        return pf.RawInline("{ref}`%s`" % target, format='markdown')
                    elif target_type in ['amsthm']:
                        return pf.RawInline("{prf:ref}`%s`" % target, format='markdown')
                    elif target_type in ['displaymath']:
                        return pf.RawInline("{eq}`%s`" % target, format='markdown')
                    else:
                        pf.debug(f"[WARNING] Link to target type {target_type} not understood.")
            else:
                pf.debug(f"[WARNING] Link to target {target} not found.")
        return elem
    if isinstance(elem, pf.CodeBlock):
        elem.attributes = {}
        return elem

    if isinstance(elem, pf.Div):
        if elem.classes:
            return create_amsmath_blocks(elem, doc)
        return elem

    if isinstance(elem, pf.Math):
        if elem.format == 'DisplayMath':
            return create_displaymath(elem, doc)
        return elem

    return elem

def finalize(doc: pf.Doc):
    # add in title labels
    for n, (elem, label) in enumerate(section_labels_to_insert.items()):
        idx = doc.content.index(elem)
        doc.content.insert(idx, pf.Para(pf.Str(f"({label.strip()})=")))

def prepare(doc: pf.Doc):
    # determine level of blocks
    block_levels = {}
    def get_level(e, d):
        if is_declarative_block(e):
            level = declarative_level(e, doc)
            block_levels[e] = level
    doc.walk(get_level)
    doc.element_levels = block_levels

    # determine labels of blocks for hyperlinks
    block_labels = {}
    def gather_labels(e, doc):
        if hasattr(e, 'identifier'):
            if e.identifier:
                block_labels[e.identifier] = e
        elif get_element_type(e) == "displaymath":
            label = "eqn"
            if '\label' in pf.stringify(e):
                label = re.findall(r"\\label\{([^\}]+)\}", e.text)[0]
            block_labels[label] = e

    doc.walk(gather_labels)
    doc.element_labels = block_labels

def main(doc=None):
    return pf.run_filter(action, doc=doc, finalize=finalize, prepare=prepare)

if __name__ == "__main__":
    main()