"""Collection of Helper Functions
"""
import textwrap
import typing as tp
import logging
import shutil
import panflute as pf

logger = logging.getLogger(__name__)

MARKDOWN_LINEBREAK_ELEM = pf.RawInline("\n", format="markdown")
TERMINAL_SIZE = shutil.get_terminal_size((80, 20))  # pass fallback
SUPPORTED_AMSTHM_BLOCKS = [
    "proof",
    "axiom",
    "theorem",
    "lemma",
    "algorithm",
    "definition",
    "remark",
    "conjecture",
    "corollary",
    "criterion",
    "example",
    "property",
    "observation",
    "proposition",
]


def break_long_string(string: str, max_len: int = 70, indent: int = 0) -> str:
    """Break long string into shorter strings of max_len (with indent added)"""
    return textwrap.indent(
        "\n".join(list(textwrap.wrap(string, max_len, break_long_words=False))),
        " " * indent,
    )


def need_linebreak(elem: pf.Element) -> tp.Tuple[bool, bool]:
    """Check if a linebreak needs to be inserted after (before) previous (next) node"""
    lb_before = (elem.prev is not None) and (
        not pf.stringify(elem.prev).endswith(("\r", "\n"))
    )
    lb_after = (elem.next is not None) and (
        not pf.stringify(elem.next).startswith(("\r", "\n"))
    )
    return lb_before, lb_after


def elem_has_multiple_figures(elem: pf.Element):
    """Check if an element is a subplot (subfigures)"""
    img_count = 0

    def is_figure(e, doc):
        nonlocal img_count
        if isinstance(e, pf.Image):
            img_count += 1

    elem.walk(is_figure)
    return img_count > 1


def get_element_type(elem: pf.Element) -> str:
    """Get Element Type"""
    if isinstance(elem, pf.Image):
        return "figure"
    if isinstance(elem, pf.Para):
        if elem_has_multiple_figures(elem):
            return "subfigures"
    if isinstance(elem, pf.Math):
        if elem.format == "DisplayMath":
            return "displaymath"
    if isinstance(elem, pf.Div):
        if elem.classes:
            if any([k in SUPPORTED_AMSTHM_BLOCKS for k in elem.classes]):
                return "amsthm"
    if isinstance(elem, pf.Header):
        return "header"
    return None


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


def get_block_identifier(
    elem: pf.Element,
    doc: pf.Doc,
    create_if_not_found: bool = False,
    block_type: str = "",
) -> str:
    """find identifier of block, create one if none exists

    Arguments:
        elem:
        doc:
        create_if_not_found: create identifier if not found
        block_type: the type of block for `elem`. Only applicable for when
          `create_if_not_found` is `True`.

    Returns
        A `str` identifier.
    """
    identifier = ""
    # 1. look for identifier, if identifier is found, return immediately
    if getattr(elem, "identifier", None):
        return elem.identifier

    # 2. look for label or name field in attributes.
    #   prioritize 'name' over 'label' since more blocks use name as key for
    #   identifier
    if getattr(elem, "attributes", None):
        _label = elem.attributes.pop("label", identifier)
        _name = elem.attributes.pop("name", identifier)
        identifier = _name if _name else _label if _label else identifier
        if identifier:
            return identifier

    # 3. create a new identifier if none exists
    if create_if_not_found:
        if not identifier:
            if not hasattr(doc, "element_labels"):
                logger.error(
                    "element_labels not initialized for Doc. Re-initializing..."
                )
                doc.element_labels = {}
            ctr = len(
                [l for l in doc.element_labels.keys() if l.startswith(block_type)]
            )
            identifier = f"{block_type}-{ctr}"
            # increment identifier until no more duplicates
            while identifier in doc.element_labels:
                ctr += 1
                identifier = f"{block_type}-{ctr}"
            doc.element_labels[identifier] = elem
    return identifier
