#!/usr/bin/env python
import re
import numpy as np
import typing as tp
import panflute as pf
from .declarative import *

__all__ = [
    'break_long_string',
    'create_image',
    'create_subplots'
]

def break_long_string(string, max_len=70, indent=0) -> str:
    """Break long string into shorter strings of max_len (with indent added)"""
    string = ' '.join(string.split(' ')) # convert multiple consecutive white spaces to single
    content = string.split(' ')
    str_len = [len(c) + 1 for c in content] # +1 for whitespace
    cum_len = np.cumsum(str_len)
    block_idx = np.floor(cum_len / max_len).astype(int)
    N_blocks = max(block_idx) + 1
    content = np.array(content, dtype=str)
    output = ""
    for b in range(N_blocks):
        idx, =  np.where(block_idx == b)
        new_line = " " * indent + ' '.join(content[idx].tolist()) + '\n'
        output += new_line
    output.rstrip('\n') # remove last newline
    return output

def create_image(elem: pf.Image, doc: pf.Doc = None) -> pf.Span:
    """Create Image Block"""
    url  = f"../{elem.url}"
    label = elem.identifier
    attr = elem.attributes
    attr_str = ""
    for name, val in attr.items():
        _match = re.findall(r"([0-9|.]*)(\\textwidth)", val)
        if _match:
            if _match[0][0]:
                val = f"{str(int(float(_match[0][0])*100))}%"
            else:
                val = "100%"
        attr_str += f":{name}: {val}\n"

    if pf.stringify(elem) == 'image': # remove default caption
        caption = []
    else:
        caption = elem.content

    content = [
        pf.Str(f"{url}\n"),
        pf.Str(f":name: {label}\n") if label else pf.Str(""),
        pf.Str(f"{attr_str}") if attr_str else pf.Str(""),
        *caption
    ]
    return create_declarative_block(elem, doc, content, 'figure', pf.Span)

def create_subplots(
    elem:pf.Para, doc: pf.Doc=None
) -> tp.Tuple[pf.Para, tp.Iterable[tp.Any]]:
    """Create Subplot using list-table and return table and substitutions to put in header"""
    if not hasattr(doc.metadata, 'substitutions'):
        doc.metadata['substitutions'] = {}
    image_ids = []
    image_content = []
    start_new_row = True
    for n, e in enumerate(elem.content):
        if isinstance(e, pf.LineBreak):
            start_new_row = True
        if isinstance(e, pf.Image):
            image_id = f"figure-{len(doc.metadata['substitutions'].content)}"
            if e.identifier:
                image_id += f":{e.identifier}"
            image_ids.append(image_id)
            assert image_id not in doc.metadata['substitutions'].content
            img = create_image(e, doc)
            doc.metadata['substitutions'].content[image_id] = pf.MetaInlines(img)
            if start_new_row:
                image_content.append(
                    pf.RawInline('* - {{%s}}\n' % image_id, format='markdown')
                )
                start_new_row = False
            else:
                image_content.append(
                    pf.RawInline('  - {{%s}}\n' % image_id, format='markdown')
                )

    label = None
    if hasattr(elem, 'identifier'):
        label = elem.identifier
    caption = ""
    if hasattr(elem, 'title'):
        caption = elem.title

    content = [
        pf.RawInline(" " + caption, format="markdown"),
        pf.RawInline(
            f'\n:label: {label}' if label is not None else '\n',
            format='markdown'
        ),
        *image_content
    ]
    return create_declarative_block(elem, doc, content, 'list-table', pf.Para)
