"""Handle LaTeX math blocks

Deals with amsthm blocks and also DisplayMath blocks and render them in formats
that are compatible with MyST syntax.
"""
import re
import typing as tp
import logging
from functools import partial
import panflute as pf
from .helpers import (
    remove_emph,
    stringify_until_match,
    TERMINAL_SIZE,
    SUPPORTED_AMSTHM_BLOCKS,
    get_block_identifier
)
from .directives import create_directive_block, create_generic_div_block

logger = logging.getLogger(__name__)


def create_amsthm_blocks(elem: pf.Div, doc: pf.Doc = None) -> pf.Para:
    """Create directive blocks that render AMSTHM

    Takes advantage of `sphinx-proof`_ sphinx extension to render
    amsthm blocks. It does the following:

    1. Walk the element to see if a `\\label{}` node is found and save that
       label. Remove that label element if found.
    2. Parses the :py:func`panflute.Div`'s stringified representation to
       see if pattern like `Theorem 1.1 (Theorem Name)` or `Example 1.1` is
       encountered. Save the theorem name `Theorem Name` if found.
    3. Render output as a :py:func:`panflute.Div` element with the
       `sphinx-proof`_ syntax.

    The output looks something like::

        ```{prf:remark} My Remark
        :label: remark-1

        This is my remark.
        ```

    .. _`sphinx-proof`: https://github.com/executablebooks/sphinx-proof
    """
    if not any([k in elem.classes for k in SUPPORTED_AMSTHM_BLOCKS]):
        logger.error(
            f"Div with class {elem.classes} not supported. "
            f"Use one of {SUPPORTED_AMSTHM_BLOCKS}."
        )
        return elem

    # find identifier in the div
    # sometimes the label for a given div can be a separate element
    # instead of a string name directly for the element.
    # identifier = elem.identifier
    # if not identifier:

    #     def get_identifier(e, doc):
    #         nonlocal identifier
    #         if isinstance(e, pf.Span):
    #             if hasattr(e, "attributes"):
    #                 if "label" in e.attributes:
    #                     identifier = e.attributes["label"]
    #                     return []
    #         return e

    #     elem.walk(get_identifier)
    # elem.identifier = identifier
    elem.identifier = get_block_identifier(elem, doc, create_if_not_found=False)

    # DEBUG: always use the first one, this could be wrong or use one
    # that's not supported
    block_type = [k for k in elem.classes if k in SUPPORTED_AMSTHM_BLOCKS]
    if len(set(block_type)) > 1:
        logger.warning(
            f"Div has multiple matching block types {set(block_type)}, "
            "using the first one."
        )
    block_type = block_type[0]
    nonumber = any([k == "nonumber" for k in elem.classes])
    if nonumber:
        elem.attributes["nonumber"] = ""
    label = ""
    elem.walk(remove_emph)

    logger.debug(f"block_type {block_type}")

    # cleanup the content of the amsthm block to remove things like
    # `Theorem 1.1 (Name of Theorem)`.
    if block_type == "proof":
        elem.replace_keyword("Proof.", pf.Str(""), 1)
    else:
        pattern = fr"({block_type.capitalize()}\ [0-9|\.\ ]*)"
        pattern_with_title = pattern + r"\(([^\)]*)\)\.?"

        # check first that the pattern is found
        if not re.findall(pattern, pf.stringify(elem)):
            logger.warning(
                "Attempted to parse amsthm label in following element "
                "but none found. This shouldn't happen with pandoc 2.11+ since "
                "a pattern of Theorem 1.1. (Name) is always generated."
            )
            logger.warning(f"{elem}")
        else:
            pat_to_remove = None
            pat_with_title = re.search(f"({pattern_with_title})", pf.stringify(elem))

            if pat_with_title:
                pat_to_remove = pat_with_title.group()
                label = pat_with_title.groups()[-1]
            else:
                pat_no_title = re.search(pattern, pf.stringify(elem))
                pat_to_remove = pat_no_title.group()
                label = ""

            # remove the label from the content of the block
            if pat_to_remove is not None:
                current_substring = []
                node_list = []

                get_substring = partial(
                    stringify_until_match,
                    current_substring=current_substring,
                    node_list=node_list,
                    match_substring=pat_to_remove,
                )
                try:
                    elem.walk(get_substring)
                except (StopIteration, RuntimeError):

                    def remove_node(e, doc):
                        if e in node_list:
                            return []
                        return e

                    elem.walk(remove_node)
                except Exception as e:
                    raise RuntimeError("Unknown Error in finding substring") from e
                else:
                    logger.error(f"{pat_to_remove} not found.")

    logger.debug(elem.content)
    # create block
    try:
        # return create_directive_block(
        #     elem, doc, elem.content, "prf:%s" % block_type, pf.Div, label=label
        # )
        return create_directive_block(
            elem, doc, elem.content, "prf:%s" % block_type, pf.Div, label=label
        )
    except Exception as e:
        # fail but do not raise
        logger.error(e, exc_info=True)


def create_displaymath(elem: pf.Math, doc: pf.Doc = None) -> pf.Span:
    """Create DisplayMath block

    Create a :py:func:`panflute.Span` block that contains the display
    math using MyST syntax that looks like::

        ```{math}
        :label: my-equation

        a = \int_1^2 u(t) dt
        ```
    """
    if not (isinstance(elem, pf.Math) and elem.format == "DisplayMath"):
        return elem

    content = elem.text
    identifier = re.search(r"\\label\{([^\}]+)\}", elem.text)
    if identifier:
        identifier = identifier.group(1)
        content = content.replace("\label{%s}" % identifier, "")
        elem.identifier = identifier
    logger.debug(f"DisplayMath Identifier: {elem.identifier}")
    return create_directive_block(
        elem, doc, [pf.RawInline(content, format="markdown")], "math", pf.Span
    )


def action(elem: pf.Element, doc: pf.Doc = None):
    """Math Actions"""
    if isinstance(elem, pf.Div):
        if elem.classes:
            if any([k in elem.classes for k in SUPPORTED_AMSTHM_BLOCKS]):
                return create_amsthm_blocks(elem, doc)
            else:
                return create_generic_div_block(elem, doc)

    if isinstance(elem, pf.Math):
        if elem.format == "DisplayMath":
            return create_displaymath(elem, doc)
        return elem


def main(doc: pf.Doc = None):
    return pf.run_filter(action, doc=doc)


if __name__ == "__main__":
    main()
