import panflute as pf
import logging
from latex_to_myst.helpers import get_element_type

logger = logging.getLogger(__name__)


def action(elem: pf.Element, doc: pf.Doc = None):
    if isinstance(elem, pf.Link):
        if not elem.attributes:
            if "http" in elem.url:
                elem.url = "".join(elem.url.split(" "))
            return elem

        if hasattr(elem, "attributes") and "reference" in elem.attributes:
            target = str(elem.attributes["reference"])

            elem.attributes = {}
            elem.url = target

            if target in doc.element_labels:
                target_elem = doc.element_labels[target]
                target_type = get_element_type(target_elem)
                if not target_type:
                    return elem
                if target_type in ["figure"]:
                    return pf.RawInline("{numref}`%s`" % target, format="markdown")
                if target_type in ["subfigures", "dislaymath", "header"]:
                    return pf.RawInline("{ref}`%s`" % target, format="markdown")
                if target_type in ["amsthm"]:
                    return pf.RawInline("{prf:ref}`%s`" % target, format="markdown")
                if target_type in ["displaymath"]:
                    return pf.RawInline("{eq}`%s`" % target, format="markdown")
                logger.error(f"Link to target type {target_type} not understood.")
            else:
                logger.error(f"Link to target {target} not found.")
                # use `{ref}` to catch all
                return pf.RawInline("{ref}`%s`" % target, format="markdown")


def main(doc: pf.Doc):
    return pf.run_filter(action, doc=doc)


if __name__ == "__main__":
    main()
