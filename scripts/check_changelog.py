import os
import re
import sys


def _get_release_version(change_name: str) -> str:
    return change_name.split(" ")[0]


def main(args) -> None:
    assert len(args) == 2, "Usage: python check_changelog.py <version>"

    version = str(args[1]).strip()
    changes_file = os.path.join(os.path.dirname(__file__), "../CHANGES.md")

    with open(changes_file, "r") as f:
        changes = f.read()

    change_entries = re.split(r"\n#+ (\d+\.\d+\.\d+.*)\n", changes)[1:]
    release_name_by_version = {
        _get_release_version(change_entries[i]): change_entries[i].strip()
        for i in range(0, len(change_entries), 2)
    }

    versions_str = "\n  ".join(list(release_name_by_version.keys())[:10])
    assert version in release_name_by_version, (
        f"Version {version} change entries not found in CHANGES.md\n\nFound entries for versions:\n"
        f"  {versions_str}\n  ..."
    )


if __name__ == "__main__":
    main(sys.argv)
