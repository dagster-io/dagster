from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from dagster_airlift._generate.generate import Stage, generate_tutorial


@pytest.mark.parametrize("stage", [val for val in Stage])
def test_generate_tutorial(stage: Stage) -> None:
    with TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        generate_tutorial(temp_dir_path, "test", stage)
        tutorial_dir = temp_dir_path / "test-tutorial"

        expected_dirs = [
            "test_tutorial",
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
