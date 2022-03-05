import json
import os
import re
import shutil
from typing import Dict

from dagster.utils import file_relative_path


def read_json(filename):
    with open(filename, encoding="utf8") as f:
        data = json.load(f)
        return data


def write_json(filename, data):
    with open(filename, "w", encoding="utf8") as f:
        json.dump(data, f, sort_keys=True)


def extract_route_from_path(path_to_folder, root, file):
    sub_path = root.replace(path_to_folder, "")[1:]
    route = sub_path.split("/") + [file.replace(".fjson", "")]
    return route


def add_data_at_route(root_data, route, data):
    curr = root_data

    for part in route[:-1]:
        if not part in curr:
            curr[part] = {}

        curr = curr[part]

    last = route[-1]
    curr[last] = data


def rewrite_relative_links(root: str, file_data: Dict[str, str]):
    """Transform relative links generated from Sphinx to work with the actual _apidocs URL.

    This method mutate the `file_data` in place.
    """

    file_body = file_data.get("body")
    if not file_body:
        return file_data

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
    root_data = {}

    for (root, _, files) in os.walk(path_to_folder):
        for filename in files:
            if filename.endswith(".fjson"):
                route = extract_route_from_path(path_to_folder, root, filename)
                data = read_json(os.path.join(root, filename))
                rewrite_relative_links(root, data)
                add_data_at_route(root_data, route, data)

    return root_data


def copy_searchindex(src_dir, dest_dir, src_file="searchindex.json", dest_file="searchindex.json"):
    """Copy searchindex.json built by Sphinx to the next directory."""
    write_json(os.path.join(src_dir, src_file), read_json(os.path.join(dest_dir, dest_file)))


def main():
    json_directory = file_relative_path(__file__, "sphinx/_build/json")
    content_dir = file_relative_path(__file__, "./content/api")

    directories_to_pack = {
        os.path.join(json_directory, "sections"): "sections.json",
        os.path.join(json_directory, "_modules"): "modules.json",
    }

    for directory, output_file in directories_to_pack.items():
        data = pack_directory_json(directory)
        write_json(os.path.join(content_dir, output_file), data)

    copy_searchindex(content_dir, json_directory)

    # objects.inv
    shutil.copyfile(
        os.path.join(json_directory, "objects.inv"),
        file_relative_path(__file__, "next/public/objects.inv"),
    )


if __name__ == "__main__":
    main()
