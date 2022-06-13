"""Directive Block Generation

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
from jinja2 import Template
from .helpers import (
    SUPPORTED_AMSTHM_BLOCKS,
    get_block_identifier,
    get_element_type,
    MARKDOWN_LINEBREAK_ELEM,
    need_linebreak,
    elem_has_multiple_figures,
)

logger = logging.getLogger(__name__)

# Jinja template for directive block
DIRECTIVE_HEADER_TEMPLATE = Template(
    """{{ '`' * (block_level + 2) }}{{ '{' }}{{ block_type }}{{ '}' }} {% if label -%}{{ label }}{%- endif %}
{% if attributes -%}
---
{% for name,val in attributes.items() -%}
{{ name }}: {{ val }}
{% endfor -%}
---
{%- endif %}
"""
)
DIRECTIVE_FOOTER_TEMPLATE = Template("""{{ '`' * (block_level + 2) }}""")


def create_generic_div_block(elem: pf.Element, doc: pf.Doc):
    """Create a Generic Div that is not of a special type"""
    classes = elem.classes
    if not classes:
        return elem

    # do nothing if content is a special directive block
    # DEBUG: Make this more robust
    if not elem.content:
        return elem
    if isinstance(elem.content[0], pf.RawBlock):
        return elem

    if any([k in SUPPORTED_AMSTHM_BLOCKS for k in classes]):
        logger.error("Attempt to create generic div block for amsthm block.")
        return elem

    return create_directive_block(
        elem,
        doc,
        content=elem.content,
        block_type="div",
        create_using=pf.Div,
        label=" ".join(classes),
    )


def create_directive_block(
    elem: pf.Element,
    doc: pf.Doc,
    content: tp.Union[pf.Element, tp.List[pf.Element]],
    block_type: str,
    create_using: pf.Element = None,
    label: str = "",
    create_identifier_if_not_found: bool = False,
) -> tp.Union[pf.Para, pf.Span]:
    """Create a directive block as literal

    Note:
        A directive block is defined as::

            ```{block_type} {label}
            :attribute1: value1
            :attribute2: value2
            {content}
            ```

    Arguments:
        elem:
        doc:
        content: a list of elements to be renderd as content of the block
        block_type: type of the directive block
        create_using: return class for the panflute node. If not specified,
          either :code:`Div` or `Span` will be used depending on whether `elem`
          if inline or block.
        label: optional label for the directive block
        create_identifier_if_not_found: whether to create a unique identifier for
          the block if label/name are not specified already.

    Returns:
        An instance :code:`create_using` representing the directive block.
    """
    content = list(content)
    if not is_directive_block(elem):
        return elem

    is_inline = issubclass(elem.__class__, pf.Inline)
    if create_using is None:
        create_using = pf.Span if is_inline else pf.Div

    # get level of block
    try:
        all_levels = doc.element_levels
        level = all_levels[elem]
    except KeyError:
        logger.error("Element level not found")
        level = directive_level(elem, doc)
        doc.element_levels[elem] = level
    except AttributeError:
        logger.error("element_levels not initialized for Doc. Recomputing...")
        level = directive_level(elem, doc)
        doc.element_levels = {elem: level}
    except Exception as e:
        logger.error(e, exc_info=True)
        return elem

    # find identifier of block, create one if none existsidentifier
    identifier = get_block_identifier(
        elem=elem,
        doc=doc,
        create_if_not_found=create_identifier_if_not_found,
        block_type=block_type,
    )

    # set identifier of the block
    attrs = {}
    if identifier:
        if (
            get_element_type(elem) in ["displaymath", "amsthm"]
        ) and block_type != "prf:proof":
            attrs["label"] = identifier
        else:
            attrs["name"] = identifier

    # set all other attributes of the block
    if getattr(elem, "attributes", None):
        attrs.update(elem.attributes)

    # generate the str for the directive block
    header = DIRECTIVE_HEADER_TEMPLATE.render(
        block_type=block_type,
        label=label,
        attributes=attrs,
        block_level=level,
    )
    footer = DIRECTIVE_FOOTER_TEMPLATE.render(
        block_level=level,
    )

    # create block
    if not is_inline:
        block_content = [
            pf.RawBlock(header, format="markdown"),
            *content,
            pf.RawBlock(footer, format="markdown"),
        ]
    else:
        need_before, need_after = need_linebreak(elem)
        block_content = [MARKDOWN_LINEBREAK_ELEM] if need_before else []
        block_content = [
            pf.RawInline(header + "\n", format="markdown"),
            *content,
            pf.RawInline("\n" + footer, format="markdown"),
        ]
        if need_after:
            block_content.append(MARKDOWN_LINEBREAK_ELEM)
        block_content = [c for c in block_content if c is not None]
    return create_using(*block_content)


def is_directive_block(elem: pf.Element) -> bool:
    """Check if an given element is a directive block"""
    return (
        (isinstance(elem, pf.Math) and elem.format == "DisplayMath")
        or isinstance(elem, pf.Div)
        or isinstance(elem, pf.Image)
        or (isinstance(elem, pf.Para) and elem_has_multiple_figures(elem))
        or (isinstance(elem, pf.Table) and elem_has_multiple_figures(elem))
    )


def directive_level(elem: pf.Element, doc: pf.Doc, starting_level: int = 0) -> int:
    """Check the nested level of a directive block starting from `starting_level`"""
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
