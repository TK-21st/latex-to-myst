import shutil
import argparse
import subprocess
import glob
from pathlib import Path
from typing import Type


def _validate_file(path: str, file_ext: str, check_exist: bool = True) -> str:
    """Validate file path according to file_ext"""
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
    # parser.add_argument(
    #     "-l",
    #     "--log",
    #     default=None,
    #     type=str,
    #     help="Logging level, default to None which turns off logging.",
    # )
    parser.add_argument(
        "-dm",
        "--default_macros",
        type=bool,
        default=True,
        help="Whether to use default macro.",
    )
    parser.add_argument(
        "-hl",
        "--highlight",
        action="store_true",
        default=True,
        help="Whether to enable syntax highlighting",
    )
    args = parser.parse_args()

    if not shutil.which("pandoc"):
        raise ModuleNotFoundError("Pandoc >= 2.11 required.")

    custom_macros = []
    if args.macro_files is not None:
        if isinstance(args.macro_files, str):
            custom_macros = [args.macro_files]
        else:
            custom_macros = args.macro_files

    macro_paths = []
    for fname in custom_macros:
        fname = _validate_file(fname, ".tex")
        macro_paths.append(Path(fname))

    CURR_PATH = Path(__file__).parent.resolve()

    fi = Path(_validate_file(args.file_in, ".tex"))
    fo = Path(_validate_file(args.file_out, ".md", check_exist=False))

    cmd = [
        "pandoc",
        str(CURR_PATH / "macros.tex") if args.default_macros else "",
        *[str(p) for p in macro_paths],
        str(fi),
        "-o",
        str(fo),
        "--filter",
        str(CURR_PATH / "main.py"),
        "-t",
        "markdown+latex_macros",
        "--markdown-headings=atx",
        "--highlight-style" if args.highlight else "",
        str(CURR_PATH / "pygments.theme") if args.highlight else "",
        "--standalone",
    ]
    subprocess.run(
        cmd,
        check=True,
    )


if __name__ == "__main__":
    main()
