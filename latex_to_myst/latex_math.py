import re
import panflute as pf
from .declarative import *

__all__ = [
    'create_amsmath_blocks',
    'create_displaymath',
    'SUPPORTED_AMSTHM_BLOCKS'
]
SUPPORTED_AMSTHM_BLOCKS = [
    'remark', 'theorem', 'example', 'lemma', 'definition', 'proof',
    'axiom', 'criterion', 'conjecture', 'corollary', 'algorithm',
    'property', 'observation', 'proposition',
    'result' # this is not supported by jupyter-proof but needed by the book
]

def remove_emph(e, doc):
    if isinstance(e, pf.Emph):
        return pf.Span(*e.content)

def create_amsmath_blocks(elem: pf.Div, doc: pf.Doc = None) -> pf.Para:
    if not any([k in elem.classes for k in SUPPORTED_AMSTHM_BLOCKS]):

        pf.debug((
            f"WARNING: Div with class {elem.classes} not supported. "
            f"Use one of {SUPPORTED_AMSTHM_BLOCKS}."
        ))
        return elem

    block_type = elem.classes[0] # DEBUG: always use the first one, this could be wrong or use one that's not supported
    nonumber = any([k=='nonumber' for k in elem.classes])
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
        pf.RawInline(f"\n:nonumber:" if nonumber else "", format='markdown'),
        pf.RawInline("\n", format='markdown'),
    ]
    elem.walk(remove_emph)
    for c in elem.content:
        content += c.content
    try:
        return create_declarative_block(elem, doc, content, 'prf:%s' % block_type, pf.Para)
    except Exception as e:
        pf.debug(elem)
        return elem
        # raise RuntimeError() from e

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