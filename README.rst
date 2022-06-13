===========================
LaTeX to MyST Pandoc Filter
===========================
Latex-to-MyST converts a given :code:`.tex` file into a :code:`.md` file using MyST syntax.

To do this, the package implements a pandoc filter that converts a subset of LaTeX
environments to MyST directives. Although it is probably more pandoc compatible
to write a custom pandoc writer instead of using :code:`RawBlocks` and :code:`RawInline` to
mimics one, the existence of :code:`panflute`_ makes it much easier for python
developers like me to work with filters instead of writers.

To use this filter, install the package by::

    pip install latex_to_myst

which adds a cli :code:`latex2myst`, which can be used to convert latex file to
myst by calling::

    latex2myst latex_file.tex markdown_file.md


LaTex Environments to MyST Directives
-------------------------------------
Latex-to-Myst Current supports:

1. All `amsthm`_ blocks,
2. Display Math
3. Subplots in the form of :code:`{list-table}`.

Many LaTeX environments need to be converted in to MyST directives.
`amsthm`_ for example, can be visualized using the *experimental*
`Sphinx-proof Directives`.

Unfortunately, MyST does not have native support for subplots, and neither
does `pandoc`_. To circumvent the problem, the best solution for now is to
use a :code:`{list-table}` directive. However, *this still needs to be fixed*
as there are some `known issues`_ that need to be addressed.


Work in Progress / Known Issues
-------------------------------
There are some `known issues`_ need to be addressed.


Credits
-------
Under the hood Latex-to-MyST uses `panflute`_ to interface with `pandoc`_.

.. _`panflute`: https://github.com/sergiocorreia/panflute
.. _`Sphinx-proof Directives`: https://sphinx-proof.readthedocs.io/en/latest/syntax.html#collection-of-directives
.. _`amsthm`: https://ctan.org/pkg/amsthm?lang=en`
.. _`known issues`: https://github.com/TK-21st/latex-to-myst/issues/1
.. _`pandoc`: https://pandoc.org/