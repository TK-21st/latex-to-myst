import os
import tempfile
from difflib import ndiff
from pathlib import Path
import subprocess
import pytest


CURR_DIR = Path(__file__).parent


@pytest.mark.parametrize("block_type", ["figure", "math", "amsthm"])
def test_basics(block_type):
    out = tempfile.NamedTemporaryFile("w+")
    subprocess.run(
        ["latex2myst", str(CURR_DIR / "sample_files" / f"{block_type}.tex"), out.name],
        check=True,
    )
    out_lines = out.readlines()
    print(out_lines)
    with open(str(CURR_DIR / "sample_files" / f"{block_type}.md")) as f:
        assert f.readlines() == out_lines, "".join(ndiff(f.readlines(), out_lines))
