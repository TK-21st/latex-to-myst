import argparse
import subprocess
from pathlib import Path
from latex_to_myst.main import main
import shutil

def main():
    parser = argparse.ArgumentParser(
        description="Convert LaTeX to MyST"
    )
    parser.add_argument(
        'file_in',
        metavar='input',
        type=str,
        help='Input LaTeX file'
    )
    parser.add_argument(
        'file_out',
        metavar='output',
        type=str,
        help='Output Markdown file'
    )
    parser.add_argument(
        '-hl',
        '--highlight',
        action='store_true',
        default=True,
        help='Whether to enable syntax highlighting'
    )
    args = parser.parse_args()

    if not shutil.which('pandoc'):
        raise ModuleNotFoundError("Pandoc >= 2.11 required.")


    fi = Path(args.file_in)
    fo = Path(args.file_out)
    CURR_PATH = Path(__file__).parent.resolve()

    assert fi.exists()
    assert fi.suffix == '.tex' or fi.suffix == ''
    assert fo.suffix == '.md' or fo.suffix == ''
    cmd = [
        "pandoc",
        str(CURR_PATH / "macros.tex"),
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
        "--standalone"
    ]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()