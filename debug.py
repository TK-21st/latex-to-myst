#!/usr/bin/env python
import re
import panflute as pf
from panflute.elements import Doc

def action(elem, doc):
    if 'Informally, under appropriate conditions (the hard part)' in pf.stringify(elem) and not isinstance(elem, pf.Doc):
        if isinstance(elem, pf.Div):
            pf.debug(elem)

def main(doc=None):
    return pf.run_filter(action, doc=doc)

if __name__ == "__main__":
    main()