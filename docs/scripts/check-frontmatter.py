# /// script
# dependencies = [
#   "python-frontmatter",
# ]
# ///
#
# Validates docs front-matter (ensures each document has `description`,
#  and each index page has `canonicalUrl` and `slug`).
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
    idx_missing_canonical_url: list[str] = []
    idx_missing_slug: list[str] = []

    for md in mds:
        fm: frontmatter.Post = frontmatter.load(md)
        if "index" in md:
            if not fm.get("canonicalUrl"):
                print(md + " missing canonicalUrl")  # noqa
                idx_missing_canonical_url.append(md)
            if not fm.get("slug"):
                print(md + " missing slug")  # noqa
                idx_missing_slug.append(md)

        if not fm.get("description"):
            print(md + " missing description")  # noqa
            mds_missing_description.append(md)

    if mds_missing_description or idx_missing_canonical_url or idx_missing_slug:
        sys.exit(1)
