import os
import tempfile
from difflib import ndiff
from pathlib import Path
import subprocess
import pytest


CURR_DIR = Path(__file__).parent


@pytest.mark.parametrize("block_type", ["figure", "math", "amsthm"])
def test_basics(block_type):
    with tempfile.TemporaryFile("w+", dir=str(CURR_DIR)) as out:
        subprocess.run(
            [
                "latex2myst",
                str(CURR_DIR / "sample_files" / f"{block_type}.tex"),
                f"{out.name}.md",
            ],
            check=True,
        )
        with open(f"{out.name}.md", "r") as real_out:
            out_lines = real_out.readlines()
        with open(str(CURR_DIR / "sample_files" / f"{block_type}.md")) as f:
            assert f.readlines() == out_lines, "".join(ndiff(f.readlines(), out_lines))
