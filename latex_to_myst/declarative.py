import panflute as pf
import typing as tp
from warnings import warn
from itertools import chain

__all__ = [
    'elem_has_multiple_figures',
    'image_in_subplot',
    'create_declarative_block',
    'is_declarative_block',
    'declarative_level',
    'SUPPORTED_AMSTHM_BLOCKS'
]

SUPPORTED_AMSTHM_BLOCKS = [
    'remark', 'theorem', 'example', 'lemma', 'definition', 'proof',
    'axiom', 'criterion', 'conjecture', 'corollary', 'algorithm',
    'property', 'observation', 'proposition',
    'result',  'center'# these are not supported by jupyter-proof but needed by the book
]


def elem_has_multiple_figures(elem: pf.Element):
    """Check if an element is a subplot (subfigures)"""
    img_count = 0
    def is_figure(e, doc):
        nonlocal img_count
        if isinstance(e, pf.Image):
            img_count += 1
    elem.walk(is_figure)
    return img_count > 1

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


def create_declarative_block(
    elem: pf.Element,
    doc: pf.Doc,
    content: tp.Iterable[pf.Element],
    block_type: str,
    create_using: tp.Union[pf.Para, pf.Span] = pf.Span,
) -> tp.Union[pf.Para, pf.Span]:
    """Create a declarative block as literal"""
    if not is_declarative_block(elem):
        return elem
    try:
        all_levels = doc.element_levels
        level = all_levels[elem]
    except KeyError:
        pf.debug("Element level not found")
        return elem
    except Exception as e:
        raise RuntimeError("Unkown error when creating declarative block") from e

    if create_using == pf.Div:
        block_content = [
            pf.RawBlock('`'*(level+2) + '{%s} ' % block_type, format='markdown'),
            *content,
            pf.RawBlock('`'*(level+2), format='markdown')
        ]
    else:
        block_content = [
            pf.RawInline('\n' + '`'*(level+2) + '{%s} ' % block_type, format='markdown'),
            *content,
            pf.RawInline('\n' + '`'*(level+2) + '\n', format='markdown')
        ]
    return create_using(*block_content)


def is_declarative_block(elem: pf.Element) -> bool:
    """Check if an given element is a declarative block"""
    return (
        (isinstance(elem, pf.Math) and elem.format == 'DisplayMath')
        or
        (isinstance(elem, pf.Div) and any([
            k in elem.classes for k in SUPPORTED_AMSTHM_BLOCKS
        ]))
        or
        isinstance(elem, pf.Image)
        or
        (isinstance(elem, pf.Para) and elem_has_multiple_figures(elem))
        or
        (isinstance(elem, pf.Table) and elem_has_multiple_figures(elem))
    )


def declarative_level(elem: pf.Element, doc:pf.Doc, starting_level: int=0) -> int:
    """Check the nested level of a declarative block"""
    if is_declarative_block(elem):
        starting_level += 1
    for child in elem._children:
        obj = getattr(elem, child)
        if isinstance(obj, pf.Element):
            return declarative_level(obj, doc, starting_level)
        elif isinstance(obj, pf.ListContainer):
            if len(obj):
                return max([declarative_level(item, doc, starting_level) for item in obj])
            else:
                return starting_level
        elif isinstance(obj, pf.DictContainer):
            if len(obj):
                return max([declarative_level(item, doc, starting_level) for item in obj.values()])
            else:
                return starting_level
        elif obj is None:
            return starting_level
        else:
            raise TypeError(type(obj))
    return starting_level