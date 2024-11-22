import gzip
import json
import os
import re
import shutil
from typing import Any


def read_json(filename: str) -> dict[str, object]:
    with open(filename, encoding="utf8") as f:
        data = json.load(f)
        assert isinstance(data, dict)
        return data


def write_json(filename: str, data: object) -> None:
    with open(filename, "w", encoding="utf8") as f:
        json.dump(data, f, sort_keys=True)


def write_json_gz(filename: str, data: object) -> None:
    with gzip.open(filename, "wt", encoding="utf-8") as gz_f:
        json.dump(data, gz_f, sort_keys=True)


def extract_route_from_path(path_to_folder: str, root: str, file: str) -> list[str]:
    sub_path = root.replace(path_to_folder, "")[1:]
    route = sub_path.split("/") + [file.replace(".fjson", "")]
    return route


def add_data_at_route(root_data, route, data):
    curr = root_data

    for part in route[:-1]:
        if part not in curr:
            curr[part] = {}

        curr = curr[part]

    last = route[-1]
    curr[last] = data


def rewrite_relative_links(root: str, file_data: dict[str, object]) -> None:
    """Transform relative links generated from Sphinx to work with the actual _apidocs URL.

    This method mutate the `file_data` in place.
    """
    file_body = file_data.get("body")
    assert isinstance(file_body, str)
    if not file_body:
        return

    # `root` can be an absolute path (eg. `/src/dagster/docs/scripts/../sphinx/_build/json/...`
    # causing the `root.startswith` logic to fail. If `root` contains `/../` split to only take the
    # relative sphinx path.
    root = root.split("/../")[-1]

    if root.startswith("sphinx/_build/json/_modules"):
        transformed = re.sub(
            r"href=\"[^\"]*\"",
            lambda matchobj: matchobj.group(0)
            .replace(r"sections/api/apidocs/", "_apidocs/")
            .replace("/#", "#"),
            file_body,
        )
    elif root.startswith("sphinx/_build/json/sections/api/apidocs/libraries"):
        transformed = re.sub(r"href=\"\.\./\.\./", 'href="../', file_body)
    else:
        transformed = re.sub(
            r"href=\"\.\./.*?(/#.*?)\"",
            lambda matchobj: matchobj.group(0).replace("/#", "#"),
            file_body,
        )

        transformed = re.sub(
            r"href=\"(\.\./)[^.]",
            lambda matchobj: matchobj.group(0).replace(matchobj.group(1), ""),
            transformed,
        )

    file_data["body"] = transformed


def pack_directory_json(path_to_folder: str):
    root_data: dict[str, Any] = {}

    for root, _, files in os.walk(path_to_folder):
        for filename in files:
            if filename.endswith(".fjson"):
                route = extract_route_from_path(path_to_folder, root, filename)
                data = read_json(os.path.join(root, filename))
                rewrite_relative_links(root, data)
                add_data_at_route(root_data, route, data)

    return root_data


def copy_searchindex(
    src_dir: str,
    dest_dir: str,
    src_file: str = "searchindex.json",
    dest_file: str = "searchindex.json.gz",
) -> None:
    """Copy searchindex.json built by Sphinx to the next directory."""
    write_json_gz(os.path.join(dest_dir, dest_file), read_json(os.path.join(src_dir, src_file)))


def main() -> None:
    sphinx_src_dir = os.path.join(os.path.dirname(__file__), "../sphinx/_build/json")
    docs_dest_dir = os.path.join(os.path.dirname(__file__), "../content/api")

    directories_to_pack = {
        os.path.join(sphinx_src_dir, "sections"): "sections.json.gz",
        os.path.join(sphinx_src_dir, "_modules"): "modules.json.gz",
    }

    for directory, output_file in directories_to_pack.items():
        data = pack_directory_json(directory)
        write_json_gz(os.path.join(docs_dest_dir, output_file), data)

    copy_searchindex(src_dir=sphinx_src_dir, dest_dir=docs_dest_dir)

    # objects.inv
    shutil.copyfile(
        os.path.join(sphinx_src_dir, "objects.inv"),
        os.path.join(os.path.dirname(__file__), "../next/public/objects.inv"),
    )

    print("Successfully packed JSON for NextJS.")  # noqa: T201


if __name__ == "__main__":
    main()
