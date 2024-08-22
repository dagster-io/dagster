import os
import pathlib
import sys

import toml

ROOT_DIR = pathlib.Path(__file__).parent.parent
VIRTUAL_ENV = ROOT_DIR / ".venv"
ROOT_PYPROJECT = ROOT_DIR / "pyproject.toml"
PYTHON = sys.executable
MIGRATED_MARKER = ".uv_migrated"


def get_projects_to_migrate():
    # find all directories with setup.py usin glob
    projects_with_setup_py = [p.parent for path in pathlib.Path(".").rglob("setup.py")]

    return projects


def cleanup_pyproject_after_pdm(file_path: str):
    # remove tool.pdb and change build backend to setuptools.build_meta

    with open(file_path, "r") as file:
        data = toml.load(file)

    if "tool" in data:
        del data["tool"]
    data["build-system"] = {
        "requires": ["hatchling"],
        "build-backend": "hatchling.build",
    }

    with open(file_path, "w") as file:
        toml.dump(data, file)


def migrate_to_uv(project_dir: pathlib.Path, run_tests: bool = False):
    project_dir = ROOT_DIR / project_dir

    # change current directory to project_dir
    os.chdir(str(project_dir))
    # convert setup.py to pyproject.toml using pdm
    os.system("pdm import -v setup.py")

    # cleanup pyproject.toml
    cleanup_pyproject_after_pdm("pyproject.toml")

    # use uv src/ layout

    with open("pyproject.toml", "r") as file:
        package_name = toml.load(file)["project"]["name"].replace("-", "_")

    os.system("mkdir -p src")
    os.system(f"cp -r {package_name} src/")

    # temporary remove the old package directory (first just move it to a temp location)
    os.system(f"mv {package_name} {package_name}-old")

    # try installing the project with uv to test if it works
    os.system("uv pip install -e .")

    if run_tests:
        # run tests
        try:
            os.system("pytest .")
        except:
            # restore the old package directory
            os.system(f"mv {package_name}-old {package_name}")
            raise

    with ROOT_PYPROJECT.open("r") as file:
        root_pyproject = toml.load(file)

    project_dir_relpath = project_dir.relative_to(ROOT_DIR)

    if str(project_dir_relpath) not in root_pyproject["tool"]["uv"]["workspace"]["members"]:
        root_pyproject["tool"]["uv"]["workspace"]["members"].append(str(project_dir_relpath))

    with ROOT_PYPROJECT.open("w") as file:
        toml.dump(root_pyproject, file)

    # delete the old package directory
    os.system(f"rm -rf {package_name}-old")

    # mark project as migrated
    (project_dir / MIGRATED_MARKER).touch()


if __name__ == "__main__":
    # os.environ["PDM_IGNORE_ACTIVE_VENV"] = "false"
    # os.environ["VIRTUAL_ENV"] = str(VIRTUAL_ENV)

    projects = [pathlib.Path("python_modules/dagster-pipes")]  # get_projects_to_migrate()

    projects = [p for p in projects if not (p / MIGRATED_MARKER).exists()]

    for project in projects:
        try:
            migrate_to_uv(project, run_tests=True)
        except Exception as e:
            print(f"Error migrating {project}: {e}")
