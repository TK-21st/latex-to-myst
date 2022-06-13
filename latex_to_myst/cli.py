"""Command Line Interface entry-point to latex2myst
"""
import io
import argparse
import logging
import panflute as pf
from pathlib import Path
from .main import ACTIONS, prepare, finalize


def _validate_file(path: str, file_ext: str, check_exist: bool = True) -> str:
    """Validate file path according to file_ext

    Arguments:
        path: a path to the file
        file_ext: the desired extension of the file that starts with :code:`.`

            .. note::

                If :code:`path` does not have an extension, then the extension
                is added to the path.

        check_exist: whether to check if file exists in addition to checking
          extension

    Raises:
        RuntimeError: Raised if
          - :code:`check_exist=True` but file not found,
          - extension mismatched between file and desired extension

    Returns:
        The path with extension.
    """
    if not Path(path).suffix:
        path += file_ext
    if check_exist and not Path(path).exists():
        raise RuntimeError(f"File '{path}' not found.")
    if Path(path).suffix != file_ext:
        raise RuntimeError(
            f"File '{path}' extension does not match desired extension '{file_ext}'. "
        )
    return path


def main():
    """Main CLI Entry Point to Latex-to-Myst

    This entry point is invoked in the command line as a console
    script and can be invoked like::

        $ latex2myst my_latex_file.tex my_new_markdown.md

    You can see the complete set of options by typing::

        $ latex2myst -h
    """
    parser = argparse.ArgumentParser(description="Convert LaTeX to MyST")
    parser.add_argument(
        "macro_files",
        metavar="macros",
        default=None,
        type=str,
        nargs="*",
        help="Names of files of macros that you'd like to use",
    )
    parser.add_argument("file_in", metavar="input", type=str, help="Input LaTeX file")
    parser.add_argument(
        "file_out", metavar="output", type=str, help="Output Markdown file"
    )
    parser.add_argument(
        "-l",
        "--log",
        default="CRITICAL",
        type=str,
        help="Logging level, default to None which turns off logging.",
    )
    parser.add_argument(
        "-dm",
        "--default_macros",
        type=bool,
        default=True,
        help="Whether to use default macro.",
    )
    args = parser.parse_args()
    logging.basicConfig(
        format="[%(asctime)s|%(name)s|%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=getattr(logging, args.log.upper()),
    )

    if pf.tools.PandocVersion().version < (2, 11):
        raise ModuleNotFoundError("Pandoc >= 2.11 required.")

    with open(Path(__file__).parent / "macros.tex", "r") as f:
        default_macros = f.read()
    macros = default_macros if args.default_macros else ""
    if args.macro_files is not None:
        macro_paths = []
        if isinstance(args.macro_files, str):
            macro_paths = [args.macro_files]
        else:
            macro_paths = args.macro_files

        for fname in macro_paths:
            fname = _validate_file(fname, ".tex")
            with open(Path(fname), "r") as f:
                macros += f.read()

    # create input, output file handles
    fi = Path(_validate_file(args.file_in, ".tex"))
    fo = Path(_validate_file(args.file_out, ".md", check_exist=False))

    logging.info(f"Parsing Input File {fi}")
    logging.info(f"Additional Macros Provided: {macro_paths}")
    logging.info(f"Using Default Macros: {args.default_macros}")
    logging.debug("Macros Used:")
    for m in macros.split("\n"):
        logging.debug(f"\t{m}")
    with open(fi, "r") as input_stream, open(fo, "w") as output_stream:
        doc = pf.convert_text(
            macros + input_stream.read(),
            input_format="latex",
            output_format="panflute",
            standalone=True,
        )
        for n, (_name, _action) in enumerate(ACTIONS):
            logging.info(f"Running {n+1}/{len(ACTIONS)} Filter: {_name}")
            try:
                doc = pf.run_filter(
                    _action,
                    doc=doc,
                    prepare=prepare if n == 0 else None,
                    finalize=finalize if n == len(ACTIONS) - 1 else None,
                )
            except Exception as e:
                logging.error(e, exc_info=True)

        output_stream.write(
            pf.convert_text(
                doc,
                input_format="panflute",
                output_format="markdown",
                standalone=True,
                extra_args=["--strip-comments"],
            )
        )


if __name__ == "__main__":
    main()
