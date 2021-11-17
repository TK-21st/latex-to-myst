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
import shutil
import panflute as pf

logger = logging.getLogger(__name__)

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
    identifier = None
    # 1. look for label or name field in attributes.
    #   prioritize 'name' over 'label' since more blocks use name as key for
    #   identifier
    if hasattr(elem, "attributes") and elem.attributes is not None:
        _label = elem.attributes.pop("label", identifier)
        if _label:
            identifier = _label
        _name = elem.attributes.pop("name", identifier)
        if _name:
            identifier = _name
    # 2. look for identifier, if identifier is found, remove everything
    if hasattr(elem, "identifier") and elem.identifier is not None:
        identifier = elem.identifier
    # 3. create a new identifier if none exists
    if not identifier or identifier is None:
        if not hasattr(doc, "element_labels"):
            logger.error("element_labels not initialized for Doc. Re-initializing...")
            doc.element_labels = {}
        ctr = len([l for l in doc.element_labels.keys() if l.startswith(block_type)])
        identifier = f"{block_type}-{ctr}"
        while identifier in doc.element_labels:
            ctr += 1
            identifier = f"{block_type}-{ctr}"
        doc.element_labels[identifier] = elem

    # set attributes of the block
    if get_element_type(elem) in ["displaymath", "amsthm"]:
        attr_str = f":label: {identifier}\n"
    else:
        attr_str = f":name: {identifier}\n"
    if hasattr(elem, "attributes") and elem.attributes is not None:
        for name, val in elem.attributes.items():
            attr_str += f":{name}: {val}\n"
    # create directive block fences
    fence_top = "`" * (level + 2) + "{%s} %s" % (block_type, label.strip(" \r\n"))
    fence_bot = f"{'`'* (level + 2)}"
    # header block should not have any empty lines within
    header = "\n".join((f"{fence_top}\n" f"{attr_str}").split("\n")).strip(" \r\n")

    def need_linebreak(neighbor, before=True):
        if before:
            if neighbor is not None:
                if not pf.stringify(neighbor).endswith(("\r", "\n")):
                    return True
            return False
        if neighbor is not None:
            if not pf.stringify(neighbor).startswith(("\r", "\n")):
                return True
        return False

    # create block
    if create_using == pf.Div:
        block_content = [
            pf.RawBlock(header, format="markdown"),
            *content,
            pf.RawBlock(fence_bot, format="markdown"),
        ]
        create_using = pf.Div
    else:
        block_content = [
            pf.RawInline("\n", format="markdown")
            if need_linebreak(elem.prev)
            else None,
            pf.RawInline(f"{header}", format="markdown"),
            pf.RawInline("\n", format="markdown"),
            *content,
            pf.RawInline("\n", format="markdown")
            if need_linebreak(content[-1])
            else None,
            pf.RawInline(f"{fence_bot}", format="markdown"),
            pf.RawInline("\n", format="markdown")
            if need_linebreak(elem.next, False)
            else None,
        ]
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
