"""This script is to ensure that we provide docs for every library that we create
"""
# pylint: disable=print-call
import os
import sys

from automation.git import git_repo_root

EXPECTED_LIBRARY_README_CONTENTS = """
# {library}

The docs for `{library}` can be found
[here](https://docs.dagster.io/_apidocs/libraries/{library_underscore}).
""".strip()


def get_library_module_directories():
    """List library module directories under python_modules/libraries.

    Returns:
        List(os.DirEntry): List of core module directories
    """
    library_module_root_dir = os.path.join(git_repo_root(), "python_modules", "libraries")
    library_directories = [
        dir_.name
        for dir_ in os.scandir(library_module_root_dir)
        if dir_.is_dir() and not dir_.name.startswith(".")
    ]
    return library_directories


def check_readme_exists(readme_file, library_name):
    """Verify that a README.md is provided for a Dagster package"""
    exists = os.path.exists(readme_file) and os.path.isfile(readme_file)
    if not exists:
        print("Missing README.md for library %s!" % library_name)
        sys.exit(1)


def check_readme_contents(readme_file, library_name):
    """Ensure README.md files have standardized contents. Some files are whitelisted until we have
    time to migrate their content to the API docs RST.
    """
    expected = EXPECTED_LIBRARY_README_CONTENTS.format(
        library=library_name, library_underscore=library_name.replace("-", "_")
    )

    with open(readme_file, "rb") as f:
        contents = f.read().decode("utf-8").strip()
        if contents != expected:
            print("=" * 100)
            print("Readme %s contents do not match!" % readme_file)
            print("expected:\n%s" % expected)
            print("\n\nfound:\n%s" % contents)
            print("=" * 100)
            sys.exit(1)


def check_api_docs(library_name):
    api_docs_root = os.path.join(git_repo_root(), "docs", "sections", "api", "apidocs", "libraries")
    underscore_name = library_name.replace("-", "_")
    if not os.path.exists(os.path.join(api_docs_root, "%s.rst" % underscore_name)):
        print("API docs not found for library %s!" % library_name)
        sys.exit(1)


def validate_library_readmes():
    dirs = get_library_module_directories()
    for library_name in dirs:
        library_root = os.path.join(git_repo_root(), "python_modules", "libraries")
        readme_file = os.path.join(library_root, library_name, "README.md")

        check_readme_exists(readme_file, library_name)

        check_readme_contents(readme_file, library_name)

        check_api_docs(library_name)

    print(":white_check_mark: All README.md contents exist and content validated!")
    print(":white_check_mark: All API docs exist!")
