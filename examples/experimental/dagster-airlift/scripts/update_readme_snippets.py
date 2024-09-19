import re
import sys
from pathlib import Path

MAIN = 'if __name__ == "__main__":'


def _get_regex_match_snippet(file_name: str) -> re.Pattern[str]:
    return re.compile(r"```python\n# " + file_name + "\n([\\S\n\t\v ]*?)\n```", re.MULTILINE)


def update_readme_snippets(readme_filepath_raw: str, *snippet_files_raw: str):
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
    snippet_files = [Path(snippet_file_raw) for snippet_file_raw in snippet_files_raw]

    readme_contents = readme_file.read_text()

    for snippet_file in snippet_files:
        snippet_contents = snippet_file.read_text()
        if MAIN in snippet_contents:
            snippet_contents = snippet_contents[: snippet_contents.index(MAIN)]
        snippet_contents = snippet_contents.replace("\\n", "\\\\n")

        file_name = snippet_file.name
        regex_match_snippet = _get_regex_match_snippet(file_name)

        if re.search(regex_match_snippet, readme_contents):
            readme_contents = re.sub(
                regex_match_snippet,
                f"```python\n# {file_name}\n{snippet_contents}\n```",
                readme_contents,
            )

    readme_file.write_text(readme_contents)


if __name__ == "__main__":
    update_readme_snippets(*sys.argv[1:])
