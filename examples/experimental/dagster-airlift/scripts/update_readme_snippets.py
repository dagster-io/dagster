import re
import sys
from pathlib import Path
from typing import Optional

from structlog import get_logger

logger = get_logger("update_readme_snippets")

MAIN = 'if __name__ == "__main__":'


def _get_regex_match_snippet(file_name: Optional[str] = None) -> re.Pattern[str]:
    file_name_capture = "(.+)" if not file_name else re.escape(file_name)
    return re.compile(
        r"```(python|yaml)\n# " + file_name_capture + "\n(?:[\\S\n\t\v ]*?)\n```", re.MULTILINE
    )


def update_readme_snippets(readme_filepath_raw: str):
    """Given a path to a README file and a list of paths to snippet files,
    update any python code blocks in the README file that match the snippet file names
    with the contents of the snippet files.

    e.g.

    ```python
    # my_snippet.py

    ...
    ```

    Will be replaced with the contents of `my_snippet.py`, if a file with that name is passed.
    """
    readme_file = Path(readme_filepath_raw)
    base_dir = readme_file.parent

    readme_contents = readme_file.read_text()

    matches = re.findall(_get_regex_match_snippet(), readme_contents)
    for file_type, file_name in matches:
        # Attempt to find the snippet file in the base dir
        snippet_file: Path = base_dir / file_name
        if not snippet_file.exists():
            raise ValueError(f"Could not find snippet file {snippet_file}.")
        snippet_contents = snippet_file.read_text()
        # Remove the MAIN block if it exists
        if MAIN in snippet_contents:
            snippet_contents = snippet_contents[: snippet_contents.index(MAIN)]
        # Fix newline escaping
        snippet_contents = snippet_contents.replace("\\n", "\\\\n")
        # Strip whitespace at the beginning and end of the snippet
        snippet_contents = snippet_contents.strip()
        readme_contents = re.sub(
            _get_regex_match_snippet(file_name),
            f"```{file_type}\n# {file_name}\n{snippet_contents}\n```",
            readme_contents,
        )

    readme_file.write_text(readme_contents)


if __name__ == "__main__":
    update_readme_snippets(*sys.argv[1:])
