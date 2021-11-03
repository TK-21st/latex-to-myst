import re
import panflute as pf
from .declarative import *

__all__ = [
    'create_amsmath_blocks',
    'create_displaymath'
]
def create_amsmath_blocks(elem: pf.Div, doc: pf.Doc = None) -> pf.Para:
    block_type = elem.classes[0]
    pattern = fr"({block_type.capitalize()}\ [0-9|\.\ ]*)"
    pattern_with_title = pattern + fr"\(([^\)]*)\)"

    pat_to_remove = re.findall(pattern, pf.stringify(elem.content[0]))
    if not pat_to_remove:
        raise RuntimeError(f"No Pattern found in AmsMath Block \n {elem}")
    pat_to_remove = pat_to_remove[0]

    pat = re.findall(
        pattern_with_title,
        pf.stringify(elem.content[0])
    )
    if pat:
        pat_to_remove = ''.join(pat[0])
        label = pat[0][1]
    else:
        label = None

    # TODO: remove the label from the content of the block

    content = [
        pf.Str(label) if label is not None else pf.Str(""),
        pf.RawInline(f"\n:label: {elem.identifier}" if elem.identifier else "", format='markdown'),
        pf.RawInline("\n", format='markdown'),
    ]
    for c in elem.content:
        content += c.content
    return create_declarative_block(elem, doc, content, 'prf:%s' % block_type, pf.Para)

def create_displaymath(elem: pf.Math, doc: pf.Doc = None) -> pf.Span:

    content = elem.text
    label = None
    if '\label' in pf.stringify(elem):
        label = re.findall(r"\\label\{([^\}]+)\}", elem.text)[0]
        content = content.replace("\label{%s}" % label, "")
    content = [
        pf.Str('\n'),
        pf.RawInline(f":label: {label}\n\n" if label is not None else "", format='markdown'),
        pf.RawInline(content, format='markdown')
    ]
    block = create_declarative_block(elem, doc, content, 'math', pf.Span)
    # pf.debug(pf.Span(pf.Str('\n'), *block.content))
    return pf.Span(pf.Str('\n'), *block.content)