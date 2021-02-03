import os

import jinja2

NEW_REPO_PLACEHOLDER = "new_repo"
NEW_REPO_PATH = os.path.join(os.path.dirname(__file__), NEW_REPO_PLACEHOLDER)


def generate_new_repo(path: str):
    """
    Generates a new repository skeleton in the filesystem at `path`.

    The name of the repository is the base of `path`.
    """
    normalized_path = os.path.normpath(path)
    repo_name = os.path.basename(normalized_path)

    os.mkdir(normalized_path)

    loader = jinja2.FileSystemLoader(searchpath=NEW_REPO_PATH)
    env = jinja2.Environment(loader=loader)

    for root, dirs, files in os.walk(NEW_REPO_PATH):
        # For each subdirectory in the source template, create a subdirectory in the destination.
        for dirname in dirs:
            src_dir_path = os.path.join(root, dirname)
            if _should_skip_file(src_dir_path):
                continue

            src_relative_dir_path = os.path.relpath(src_dir_path, NEW_REPO_PATH)
            dst_relative_dir_path = src_relative_dir_path.replace(
                NEW_REPO_PLACEHOLDER,
                repo_name,
                1,
            )
            dst_dir_path = os.path.join(normalized_path, dst_relative_dir_path)

            os.mkdir(dst_dir_path)

        # For each file in the source template, render a file in the destination.
        for filename in files:
            src_file_path = os.path.join(root, filename)
            if _should_skip_file(src_file_path):
                continue

            src_relative_file_path = os.path.relpath(src_file_path, NEW_REPO_PATH)
            dst_relative_file_path = src_relative_file_path.replace(
                NEW_REPO_PLACEHOLDER,
                repo_name,
                1,
            )
            dst_file_path = os.path.join(normalized_path, dst_relative_file_path)

            if dst_file_path.endswith(".tmpl"):
                dst_file_path = dst_file_path[: -len(".tmpl")]

            with open(dst_file_path, "w") as f:
                template = env.get_template(name=src_relative_file_path)
                f.write(template.render(repo_name=repo_name))
                f.write("\n")


def _should_skip_file(path):
    """
    Given a file path `path` in a source template, returns whether or not the file should be skipped
    when generating destination files.

    Technically, `path` could also be a directory path that should be skipped.
    """
    if "__pycache__" in path:
        return True

    if ".pytest_cache" in path:
        return True

    if ".egg-info" in path:
        return True

    if ".DS_Store" in path:
        return True

    return False
