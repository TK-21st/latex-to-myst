"""Handle LaTeX math blocks

Deals with amsthm blocks and also DisplayMath blocks and render them in formats
that are compatible with MyST syntax.
"""
import re
import typing as tp
import logging
from functools import partial
import panflute as pf
from .directive import (
    create_directive_block,
    SUPPORTED_AMSTHM_BLOCKS,
)

logger = logging.getLogger(__name__)

__all__ = ["create_amsthm_blocks", "create_displaymath"]


def remove_emph(e: pf.Element, doc: pf.Doc):
    """Convert all Emph to Span

    By default all amsthm blocks are shown in italics in LaTeX.
    This will convert all of them into :py:func:`Span` components.
    """
    if isinstance(e, pf.Emph):
        return pf.Span(*e.content)
    return e


# panflute elements that render to horizontal spaces
HorizontalSpaces = (pf.Space, pf.LineBreak, pf.SoftBreak)
# panflute elements that render to vertical spaces
VerticalSpaces = (pf.Para,)


def stringify_until_match(
    elem: pf.Element,
    doc: pf.Doc,
    current_substring: tp.List[str],
    node_list: tp.List[pf.Element],
    match_substring: str,
) -> None:
    """Stringify element until the desired substring is matched

    Arguments:
        elem: panflute element that is being walked right now
        doc: document (not used, added for call signature of
          :py:func:`panflute.Element.walk`)
        current_substring: a list of current substrings corresponding to all
          previously walked nodes
        node_list: a list of nodes that have been walked
        match_substring: the desired substring to match

    Raises:
        StopIteration: raised when the desired substring is matched

    Example:

        >>> current_substring = []
        >>> node_list = []
        >>> desired_substring = "I want this string"
        >>> get_substring = partial(
                stringify_until_match,
                current_substring=current_substring,
                node_list=node_list,
                match_substring = match_substring
            )
        >>> try:
                starting_element.walk(get_substring)
            except (StopIteration, RuntimeError):
                def remove_node(e, doc):
                    if e in node_list:
                        return []
                elem.walk(remove_node)
            except Exception as e:
                raise RuntimeError("Unknown Error in finding substring") from e
            else:
                logger.error(f"{desired_substring} not found.")

    .. note::

        This function is adapted from `panflute.stringify`_.

    .. `panflute.stringify`: https://github.com/sergiocorreia/panflute/blob/281ddeaebd2c2c94f457f3da785037cadf69389e/panflute/tools.py#L215
    """
    if hasattr(elem, "text"):
        ans = elem.text
    elif isinstance(elem, HorizontalSpaces):
        ans = " "
    elif isinstance(elem, VerticalSpaces):
        ans = "\n\n"
    elif isinstance(elem, pf.Citation):
        ans = ""
    else:
        ans = ""

    # Add quotes around the contents of Quoted()
    if isinstance(elem.parent, pf.Quoted):
        if elem.index == 0:
            ans = '"' + ans
        if elem.index == len(elem.container) - 1:
            ans += '"'

    current_substring.append(ans)
    node_list.append(elem)
    if "".join(current_substring).strip() == match_substring.strip():
        raise StopIteration


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
            (
                f"Div with class {elem.classes} not supported. "
                f"Use one of {SUPPORTED_AMSTHM_BLOCKS}."
            )
        )
        return elem

    identifier = elem.identifier
    if not identifier:

        def get_identifier(e, doc):
            nonlocal identifier
            if isinstance(e, pf.Span):
                if hasattr(e, "attributes"):
                    if "label" in e.attributes:
                        identifier = e.attributes["label"]
                        return []
            return e

        elem.walk(get_identifier)

    # DEBUG: always use the first one, this could be wrong or use one
    # that's not supported
    block_type = elem.classes[0]
    nonumber = any([k == "nonumber" for k in elem.classes])
    label = ""
    elem.walk(remove_emph)
    if block_type == "proof":
        elem.replace_keyword("Proof.", pf.Str(""), 1)
    elif block_type == "center":
        pass  # do nothing for center
    else:
        pattern = fr"({block_type.capitalize()}\ [0-9|\.\ ]*)"
        pattern_with_title = pattern + r"\(([^\)]*)\)\.?"

        if not re.findall(pattern, pf.stringify(elem.content[0])):
            raise RuntimeError(f"No Pattern found in AMSTHM Block \n {elem}")

        pat = re.findall(pattern_with_title, pf.stringify(elem.content[0]))
        pat_to_remove = None
        if pat:
            pat_to_remove = re.findall(
                f"({pattern_with_title})", pf.stringify(elem.content[0])
            )[0][0]
            label = pat[0][1]
        else:
            pat_to_remove = re.findall(pattern, pf.stringify(elem.content[0]))[0]
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

    content = []

    if identifier:
        content.append(pf.RawBlock(f":label: {identifier}", format="markdown"))
    if nonumber:
        content.append(pf.RawBlock(":nonumber:" if nonumber else "", format="markdown"))

    content += elem.content
    try:
        return create_directive_block(
            elem, doc, content, "prf:%s" % block_type, pf.Div, label=label
        )
    except Exception as e:
        logger.error(elem)
        raise RuntimeError() from e


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
    identifier = None
    if "\label" in pf.stringify(elem):
        identifier = re.findall(r"\\label\{([^\}]+)\}", elem.text)[0]
        content = content.replace("\label{%s}" % identifier, "")
    content = [
        pf.SoftBreak,
        pf.RawInline(
            f":label: {identifier}\n" if identifier is not None else "",
            format="markdown",
        ),
        pf.SoftBreak,
        pf.RawInline(content, format="markdown"),
    ]
    block = create_directive_block(elem, doc, content, "math", pf.Span)
    return pf.Span(pf.Str("\n"), *block.content)
