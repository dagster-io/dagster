import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from dagster_airlift._generate.generate import Stage


@pytest.mark.parametrize("stage", [val for val in Stage])
def test_generate_tutorial(stage: Stage) -> None:
    with TemporaryDirectory() as temp_dir:
        subprocess.run(
            ["dagster-airlift", "examples", "tutorial", temp_dir, "--stage", stage.value],
            check=False,
        )
        temp_dir_path = Path(temp_dir)
        tutorial_dir = temp_dir_path / "example-tutorial"

        expected_dirs = [
            "example_tutorial",
            "data",
            "scripts",
        ]

        expected_files = [
            "setup.py",
            ".gitignore",
            "Makefile",
            "pyproject.toml",
        ]

        assert sorted([d.name for d in tutorial_dir.iterdir() if d.is_dir()]) == sorted(
            expected_dirs
        )
        assert sorted([f.name for f in tutorial_dir.iterdir() if f.is_file()]) == sorted(
            expected_files
        )
