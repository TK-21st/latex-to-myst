"""Collection of Helpers to create directive blocks consistent with MyST syntax

The syntax for MyST `Directive Blocks`_ that is followed in this repository takes
the form of::

    ```{directivename} arg1 arg2
    :key1: metadata1
    :key2: metadata2
    My directive content.
    ```

.. _`Directive Blocks`: https://jupyterbook.org/content/myst.html#directives
"""
import typing as tp
import logging
import panflute as pf

__all__ = [
    "elem_has_multiple_figures",
    "image_in_subplot",
    "create_directive_block",
    "is_directive_block",
    "directive_level",
    "SUPPORTED_AMSTHM_BLOCKS",
]
logger = logging.getLogger(__name__)

SUPPORTED_AMSTHM_BLOCKS = [
    "remark",
    "theorem",
    "example",
    "lemma",
    "definition",
    "proof",
    "axiom",
    "criterion",
    "conjecture",
    "corollary",
    "algorithm",
    "property",
    "observation",
    "proposition",
    "result",
    "center",  # these are not supported by jupyter-proof but needed by the book
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


def create_directive_block(
    elem: pf.Element,
    doc: pf.Doc,
    content: tp.Iterable[pf.Element],
    block_type: str,
    create_using: tp.Union[pf.Para, pf.Span] = pf.Span,
    label: str = "",
) -> tp.Union[pf.Para, pf.Span]:
    """Create a directive block as literal"""
    if not is_directive_block(elem):
        return elem

    # get level of block
    try:
        all_levels = doc.element_levels
        level = all_levels[elem]
    except KeyError:
        logger.error("Element level not found")
        return elem
    except Exception as e:
        raise RuntimeError("Unkown error when creating directive block") from e

    # create block
    if create_using == pf.Div:
        block_content = [
            pf.RawBlock(
                "`" * (level + 2) + "{%s} %s" % (block_type, label), format="markdown"
            ),
            *content,
            pf.RawBlock("`" * (level + 2), format="markdown"),
        ]
    else:
        block_content = [
            pf.SoftBreak,
            pf.RawInline(
                "`" * (level + 2) + "{%s} %s\n" % (block_type, label),
                format="markdown",
            ),
            *content,
            pf.RawInline(f"\n{'`'* (level + 2)}\n", format="markdown"),
        ]
    return create_using(*block_content)


def is_directive_block(elem: pf.Element) -> bool:
    """Check if an given element is a directive block"""
    return (
        (isinstance(elem, pf.Math) and elem.format == "DisplayMath")
        or (
            isinstance(elem, pf.Div)
            and any([k in elem.classes for k in SUPPORTED_AMSTHM_BLOCKS])
        )
        or isinstance(elem, pf.Image)
        or (isinstance(elem, pf.Para) and elem_has_multiple_figures(elem))
        or (isinstance(elem, pf.Table) and elem_has_multiple_figures(elem))
    )


def directive_level(elem: pf.Element, doc: pf.Doc, starting_level: int = 0) -> int:
    """Check the nested level of a directive block"""
    if is_directive_block(elem):
        starting_level += 1
    for child in elem._children:
        obj = getattr(elem, child)
        if isinstance(obj, pf.Element):
            return directive_level(obj, doc, starting_level)
        elif isinstance(obj, pf.ListContainer):
            if len(obj):
                return max([directive_level(item, doc, starting_level) for item in obj])
            else:
                return starting_level
        elif isinstance(obj, pf.DictContainer):
            if len(obj):
                return max(
                    [
                        directive_level(item, doc, starting_level)
                        for item in obj.values()
                    ]
                )
            else:
                return starting_level
        elif obj is None:
            return starting_level
        else:
            raise TypeError(type(obj))
    return starting_level
