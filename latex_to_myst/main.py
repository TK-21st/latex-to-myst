#!/usr/bin/env python
import panflute as pf
from latex_to_myst.latex_math import *
from latex_to_myst.figures import *
from latex_to_myst.declarative import *

section_labels_to_insert = {}

def action(elem: pf.Element, doc: pf.Doc = None) -> pf.Element:
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
        label = elem.identifier
        section_labels_to_insert[elem.index] = label
        elem.identifier = ""
        elem.classes = []
        return elem

    if isinstance(elem, pf.Para):
        if para_is_subplot(elem):
            return create_subplots(elem, doc)
        return elem

    if isinstance(elem, pf.Image):
        if image_in_subplot(elem):
            return elem
        return create_image(elem, doc)

    if isinstance(elem, pf.Link):
        if hasattr(elem, 'attributes') and 'reference' in elem.attributes:
            target = str(elem.attributes['reference'])
            reftype= elem.attributes['reference-type']
            elem.attributes = {}
            elem.url = target
            if reftype == 'eqref':
                elem.content = [pf.Str("")]
            else: # section and figures
                if target.startswith('fig'):
                    return pf.RawInline("{numref}`%s`" % target, format='markdown')
                elif target.startswith('sec'):
                    return pf.RawInline("{ref}`%s`" % target, format='markdown')
                else:
                    return elem

        if 'http' in elem.url:
            elem.url = ''.join(elem.url.split(' '))
        return elem
    if isinstance(elem, pf.CodeBlock):
        elem.attributes = {}
        return elem

    if isinstance(elem, pf.Div) and any([
        k in elem.classes for k in ['remark', 'theorem', 'example', 'lemma', 'definition']
    ]):
        return create_amsmath_blocks(elem, doc)

    if isinstance(elem, pf.Math):
        if elem.format == 'DisplayMath':
            return create_displaymath(elem, doc)
        return elem

    return elem

def finalize(doc: pf.Doc):
    # add in title labels
    for n, (idx, label) in enumerate(section_labels_to_insert.items()):
        doc.content.insert(n + idx, pf.Para(pf.Str(f"({label})=")))

def prepare(doc: pf.Doc):
    # determine level of blocks
    block_levels = {}
    def get_level(e, d):
        if is_declarative_block(e):
            level = declarative_level(e, doc)
            block_levels[e] = level
    doc.walk(get_level)
    doc.element_levels = block_levels
    # doc.metadata['substitutions'] =

def main(doc=None):
    return pf.run_filter(action, doc=doc, finalize=finalize, prepare=prepare)

if __name__ == "__main__":
    main()