from pathlib import Path

from automation.utils import discover_git_root, get_all_repo_packages, git_ls_files, pushd


# We want to make sure all of our packages are published with `py.typed` files unless explicitly
# excluded.
def test_all_packages_have_py_typed():
    git_root = discover_git_root(Path(__file__))
    with pushd(git_root):
        package_roots = get_all_repo_packages()
        missing_py_typed_file = []
        missing_py_typed_in_manifest_in = []
        for package_root in package_roots:
            root_python_package = _find_root_python_package(package_root)
            if not (root_python_package / "py.typed").exists():
                missing_py_typed_file.append(str(package_root))

            not_published_packages = [
                "automation",
                "dagster-test",
                "kitchen-sink",  # in dagster-airlift
                "perf-harness",  # in dagster-airlift
            ]

            # Published packages are additionally required to include py.typed in MANIFEST.in to ensure
            # they are included in the published distribution.
            if (
                str(package_root).startswith("python_modules")
                and package_root.name not in not_published_packages
            ):
                manifest_in = package_root / "MANIFEST.in"
                assert manifest_in.exists(), f"MANIFEST.in is missing for: {package_root}"
                if "py.typed" not in manifest_in.read_text():
                    with open(manifest_in) as f:
                        if "py.typed" not in f.read():
                            missing_py_typed_in_manifest_in.append(str(package_root))

        nl = "\n"
        assert (
            not missing_py_typed_file
        ), f"Missing py.typed files in these packages:\n{nl.join(missing_py_typed_file)}"
        assert not missing_py_typed_in_manifest_in, f"Missing py.typed in MANIFEST.in for these packages:\n{nl.join(missing_py_typed_in_manifest_in)}"


def _find_root_python_package(package_root: Path) -> Path:
    standard_name = package_root / package_root.name.replace("-", "_")
    if standard_name.exists():
        return standard_name
    else:
        with pushd(package_root):
            init_pys = git_ls_files("*/__init__.py")
            packages = [Path(p).parent for p in init_pys]
            return next(package_root / p for p in packages if not p.name.endswith("_tests"))
