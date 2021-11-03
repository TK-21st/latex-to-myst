import panflute as pf
import typing as tp
from warnings import warn
from itertools import chain

__all__ = [
    'para_is_subplot',
    'image_in_subplot',
    'create_declarative_block',
    'is_declarative_block',
    'declarative_level'
]
def para_is_subplot(elem: pf.Para):
    """Check if a paragraph is a subplot (subfigures)"""
    if sum([isinstance(o, pf.Image) for o in elem.content]) > 1:
        return True
    return False

def image_in_subplot(elem: pf.Image):
    """Check if an image node is in subplot"""
    if isinstance(elem.parent, pf.Para):
        return para_is_subplot(elem.parent)
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
            k in elem.classes for k in [
                'theorem','result','proposition','lemma','assumption','corollary',
                'definition','remark','example','algorithm'
            ]
        ]))
        or
        isinstance(elem, pf.Image)
        or
        (isinstance(elem, pf.Para) and para_is_subplot(elem))
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
            return max([declarative_level(item, doc, starting_level) for item in obj])
        elif isinstance(obj, pf.DictContainer):
            return max([declarative_level(item, doc, starting_level) for item in obj.values()])
        elif obj is None:
            return starting_level
        else:
            raise TypeError(type(obj))
    return starting_level