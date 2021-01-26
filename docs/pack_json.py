import json
import os

from dagster.utils import file_relative_path


def read_json(filename):
    with open(filename) as f:
        data = json.load(f)
        return data


def write_json(filename, data):
    with open(filename, "w") as f:
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


def pack_directory_json(path_to_folder: str):
    root_data = {}

    for (root, _, files) in os.walk(path_to_folder):
        for file in files:
            if file.endswith(".fjson"):
                route = extract_route_from_path(path_to_folder, root, file)
                data = read_json(os.path.join(root, file))
                add_data_at_route(root_data, route, data)

    return root_data


def main():
    json_directory = file_relative_path(__file__, "sphinx/_build/json")
    content_master_directory = file_relative_path(__file__, "next/content/api")

    directories_to_pack = {
        os.path.join(json_directory, "sections"): "sections.json",
        os.path.join(json_directory, "_modules"): "modules.json",
    }

    for directory, output_file in directories_to_pack.items():
        data = pack_directory_json(directory)
        write_json(os.path.join(content_master_directory, output_file), data)


if __name__ == "__main__":
    main()
