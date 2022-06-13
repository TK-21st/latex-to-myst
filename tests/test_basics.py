import os
import tempfile
from difflib import ndiff
from pathlib import Path
import subprocess
import pytest


CURR_DIR = Path(__file__).parent


@pytest.mark.parametrize("block_type", ["figure", "math", "amsthm"])
def test_basics(block_type):
    with tempfile.TemporaryDirectory() as dir:
        out_path = Path(dir) / f"{block_type}.md"
        subprocess.run(
            [
                "latex2myst",
                str(CURR_DIR / "sample_files" / f"{block_type}.tex"),
                str(out_path),
            ],
            check=True,
        )
        with open(out_path, "r") as real_out:
            out_lines = real_out.readlines()
        with open(str(CURR_DIR / "sample_files" / f"{block_type}.md")) as f:
            assert f.readlines() == out_lines, "".join(ndiff(f.readlines(), out_lines))
