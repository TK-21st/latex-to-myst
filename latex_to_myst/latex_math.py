import re
import panflute as pf
from functools import partial
from panflute.elements import Subscript
from .declarative import *
__all__ = [
    'create_amsmath_blocks',
    'create_displaymath'
]

def remove_emph(e, doc):
    """Convert all Emph to Span"""
    if isinstance(e, pf.Emph):
        return pf.Span(*e.content)

HorizontalSpaces = (pf.Space, pf.LineBreak, pf.SoftBreak)

VerticalSpaces = (pf.Para, )


def create_amsmath_blocks(elem: pf.Div, doc: pf.Doc = None) -> pf.Para:
    if not any([k in elem.classes for k in SUPPORTED_AMSTHM_BLOCKS]):
        pf.debug((
            f"[WARNING] Div with class {elem.classes} not supported. "
            f"Use one of {SUPPORTED_AMSTHM_BLOCKS}."
        ))
        return elem

    identifier = elem.identifier
    if not identifier:
        def get_identifier(e, doc):
            nonlocal identifier
            if isinstance(e, pf.Span):
                if hasattr(e, 'attributes'):
                    if 'label' in e.attributes:
                        identifier = e.attributes['label']
                        return []
        elem.walk(get_identifier)

    block_type = elem.classes[0] # DEBUG: always use the first one, this could be wrong or use one that's not supported
    nonumber = any([k=='nonumber' for k in elem.classes])
    label = ""
    elem.walk(remove_emph)
    if block_type == 'proof':
        elem.replace_keyword('Proof.', pf.Str(""), 1)
    elif block_type == 'center':
        pass # do nothing for center
    else:
        pattern = fr"({block_type.capitalize()}\ [0-9|\.\ ]*)"
        pattern_with_title = pattern + fr"\(([^\)]*)\)\.?"

        if not re.findall(pattern, pf.stringify(elem.content[0])):
            raise RuntimeError(f"No Pattern found in AMSTHM Block \n {elem}")

        pat = re.findall(
            pattern_with_title,
            pf.stringify(elem.content[0])
        )
        pat_to_remove = None
        if pat:
            pat_to_remove = re.findall(
                f"({pattern_with_title})",
                pf.stringify(elem.content[0])
            )[0][0]
            label = pat[0][1]
        else:
            pat_to_remove = re.findall(
                pattern,
                pf.stringify(elem.content[0])
            )[0]
            label = ""


        # remove the label from the content of the block
        if pat_to_remove is not None:
            def attach_str(e, doc, answer, node_list):
                if hasattr(e, 'text'):
                    ans = e.text
                elif isinstance(e, HorizontalSpaces):
                    ans = ' '
                elif isinstance(e, VerticalSpaces):
                    ans = '\n\n'
                elif type(e) == pf.Citation:
                    ans = ''
                else:
                    ans = ''

                # Add quotes around the contents of Quoted()
                if type(e.parent) == pf.Quoted:
                    if e.index == 0:
                        ans = '"' + ans
                    if e.index == len(e.container) - 1:
                        ans += '"'

                answer.append(ans)
                node_list.append(e)
                if ''.join(answer).strip() == pat_to_remove.strip():
                    raise StopIteration

            answer = []
            node_list = []
            f = partial(attach_str, answer=answer, node_list=node_list)
            try:
                elem.walk(f)
            except (StopIteration, RuntimeError):
                def remove_node(e, doc):
                    if e in node_list:
                        return []
                elem.walk(remove_node)
            except Exception as e:
                raise RuntimeError() from e
            else:
                pf.debug(f"[WARNING] {pat_to_remove} not found.")

    content = []

    if identifier:
        content.append(pf.RawBlock(f":label: {identifier}", format='markdown'))
    if nonumber:
        content.append(pf.RawBlock(f":nonumber:" if nonumber else "", format='markdown'))

    content += elem.content
    try:
        return create_declarative_block(elem, doc, content, 'prf:%s' % block_type, pf.Div, label=label)
    except Exception as e:
        pf.debug(elem)
        raise RuntimeError() from e

def create_displaymath(elem: pf.Math, doc: pf.Doc = None) -> pf.Span:

    content = elem.text
    identifier = None
    if '\label' in pf.stringify(elem):
        identifier = re.findall(r"\\label\{([^\}]+)\}", elem.text)[0]
        content = content.replace("\label{%s}" % identifier, "")
    content = [
        pf.SoftBreak,
        pf.RawInline(f":label: {identifier}\n" if identifier is not None else "", format='markdown'),
        pf.SoftBreak,
        pf.RawInline(content, format='markdown')
    ]
    block = create_declarative_block(elem, doc, content, 'math', pf.Span)
    return pf.Span(pf.Str('\n'), *block.content)