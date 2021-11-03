import re
import panflute as pf
from .declarative import *

__all__ = [
    'create_amsmath_blocks',
    'create_displaymath'
]

def remove_emph(e, doc):
    """Convert all Emph to Span"""
    if isinstance(e, pf.Emph):
        return pf.Span(*e.content)


def create_amsmath_blocks(elem: pf.Div, doc: pf.Doc = None) -> pf.Para:
    if not any([k in elem.classes for k in SUPPORTED_AMSTHM_BLOCKS]):
        pf.debug((
            f"[WARNING] Div with class {elem.classes} not supported. "
            f"Use one of {SUPPORTED_AMSTHM_BLOCKS}."
        ))
        return elem

    block_type = elem.classes[0] # DEBUG: always use the first one, this could be wrong or use one that's not supported
    nonumber = any([k=='nonumber' for k in elem.classes])
    label = None
    if block_type == 'proof':
        elem.replace_keyword('Proof.', pf.Str(""), 1)
    elif block_type == 'center':
        pass # do nothing for center
    else:
        pattern = fr"({block_type.capitalize()}\ [0-9|\.\ ]*)"
        pattern_with_title = pattern + fr"\(([^\)]*)\)"

        pat_to_remove = re.findall(pattern, pf.stringify(elem.content[0]))
        if not pat_to_remove:
            raise RuntimeError(f"No Pattern found in AMSTHM Block \n {elem}")
        pat_to_remove = pat_to_remove[0]

        pat = re.findall(
            pattern_with_title,
            pf.stringify(elem.content[0])
        )
        if pat:
            pat_to_remove = ''.join(pat[0])
            label = pat[0][1]

    # TODO: remove the label from the content of the block
    content = []
    if label:
        content.append(pf.RawBlock(label, format="markdown"))
    if elem.identifier:
        content.append(pf.RawBlock(f":label: {elem.identifier}", format='markdown'))
    if nonumber:
        content.append(pf.RawBlock(f":nonumber:" if nonumber else "", format='markdown'))
    elem.walk(remove_emph)
    content += elem.content
    try:
        return create_declarative_block(elem, doc, content, 'prf:%s' % block_type, pf.Div)
    except Exception as e:
        pf.debug(elem)
        raise RuntimeError() from e

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
    return pf.Span(pf.Str('\n'), *block.content)