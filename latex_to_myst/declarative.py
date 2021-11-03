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
        pf.RawInline('`'*(level+2) + '{%s} ' % block_type, format='markdown'),
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
        if starting_level == 0:
            pf.debug("-----------------------\n", elem)
    for child in elem._children:
        obj = getattr(elem, child)
        if isinstance(obj, pf.Element):
            return declarative_level(obj, doc, starting_level)
        elif isinstance(obj, pf.ListContainer):
            pf.debug("\t", starting_level, "\t", obj)
            l = (declarative_level(item, doc, starting_level) for item in obj)
            # We need to convert single elements to iterables, so that they
            # can be flattened later
            l = ((item,) if type(item) != list else item for item in l)
            # Flatten the list, by expanding any sublists
            # l = list(chain.from_iterable(ans))
            return sum(list(chain.from_iterable(l)))
            # return sum([declarative_level(item, starting_level) for item in obj])
        elif isinstance(obj, pf.DictContainer):
            return sum([declarative_level(item, doc, starting_level) for item in obj.values()])
        elif obj is None:
            pf.debug('None', starting_level, obj)
            return starting_level
        else:
            raise TypeError(type(obj))
    if is_declarative_block(elem):
        starting_level += 1
    return starting_level