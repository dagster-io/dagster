"""Identify missing Sphinx references for `.mdx` docs.


PREREQUISITES

    make apidoc-build

USAGE

    python scripts/validate-pyobjects.py


"""
import json
import re
from glob import glob
from typing import Dict, List

# Location of Sphinx index; requires building Sphinx docs beforehand
SPHINX_INDEX_PATH = "sphinx/_build/json/searchindex.json"

# Extract `object` and `module` from `PyObject` components in `.mdx` files
PYOBJECT_PATTERN = r'<PyObject (?:object="([\w\d]+)"\s*)?(?:module="([\w\d]+)"\s*)?/>'


def extract_pyobject_object_and_module() -> Dict[str, List[dict]]:
    """Finds all <PyObject> components in MDX files and return mapping of file to object/module."""
    mdx_files = glob("**/*.mdx", recursive=True)
    references = {}
    for f in mdx_files:
        content = open(f, "r").read().replace("\n", " ")
        matches = [
            {"object": m.group(1), "module": m.group(2)}
            for m in re.finditer(PYOBJECT_PATTERN, content)
        ]
        if matches:
            references[f] = matches
    return references


def get_sphinx_search_index() -> Dict:
    """Loads Sphinx JSON search index."""
    return json.load(open(SPHINX_INDEX_PATH))


if __name__ == "__main__":
    references = extract_pyobject_object_and_module()

    sphinx_index = get_sphinx_search_index()

    for file, pyobjects in references.items():
        for pyobj in pyobjects:
            _object = pyobj["object"]
            _module = pyobj["module"] if pyobj["module"] else "dagster"
            sphinx_module = sphinx_index["objects"][_module]
            sphinx_module_objects = [
                o[4] for o in sphinx_module
            ]  # Example object entry: [[74, 0, 1, '', 'AddDynamicPartitionsRequest'], ...]
            if _object not in [o[4] for o in sphinx_module]:
                print(f"{_module:<20} {_object:<25} {file}")  # noqa: T201
