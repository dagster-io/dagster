# /// script
# dependencies = [
#   "python-frontmatter",
# ]
# ///
#
# Validates docs front-matter (ensures each document has `description`).
#
# USAGE
#
#     uv run scripts/check-frontmatter.py
#

import sys
from glob import glob

import frontmatter

EXCLUDED_PATH_PREFIXES = [
    "docs/partials/",
]


if __name__ == "__main__":
    mds1 = glob("docs/**/*.md", recursive=True)
    mds2 = glob("docs/**/*.mdx", recursive=True)
    mds = mds1 + mds2

    # filter excluded path prefixes
    mds = [md for md in mds if not any(md.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES)]

    mds_missing_description: list[str] = []
    for md in mds:
        fm: frontmatter.Post = frontmatter.load(md)
        if not fm.get("description"):
            print(md)  # noqa
            mds_missing_description.append(md)

    if mds_missing_description:
        sys.exit(1)
