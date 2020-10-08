import itertools
import os
import subprocess

import click
import packaging.version
from automation.git import get_git_tag, git_repo_root
from automation.utils import all_equal, check_output

from .dagster_module import DagsterModule
from .utils import format_module_versions

# The root modules managed by this script
CORE_MODULE_NAMES = ["dagster", "dagit", "dagster-graphql"]


class DagsterModulePublisher:
    def __init__(self):
        # Removed hard-coded list in favor of automatic scan of libraries folder
        # List of subdirectories in directory: https://stackoverflow.com/a/973488
        self.library_module_names = set(
            next(os.walk(os.path.join(git_repo_root(), "python_modules", "libraries")))[1]
        )

        # Construct list of core modules
        self.core_modules = []
        for name in CORE_MODULE_NAMES:
            additional_steps = ["./build_js.sh"] if name == "dagit" else None
            self.core_modules.append(
                DagsterModule(name, is_library=False, additional_steps=additional_steps)
            )

        # Construct list of library modules, some of which may not be published
        self.library_modules = [
            DagsterModule(name, is_library=True) for name in self.library_module_names
        ]

        self.all_modules = self.core_modules + self.library_modules
        self.all_publishable_modules = [m for m in self.all_modules if m.should_publish]

    @property
    def all_module_versions(self):
        """Gather the version info from version.py files for all publishable modules

        Returns:
            List[dict]: List of dictionaries of version info
        """
        return {module.name: module.get_version_info() for module in self.all_publishable_modules}

    def check_for_cruft(self, autoclean):
        """We need to ensure directories don't have spurious files in them before publishing to
        PyPI.

        Args:
            autoclean (bool): Should the script automatically clean up (remove) extraneous files?

        Raises:
            Exception: Raised when we aren't able to resolve cruft issues
        """
        found_cruft = list(
            itertools.chain.from_iterable(module.find_cruft() for module in self.all_modules)
        )

        if found_cruft:
            if autoclean:
                wipeout = "!"
            else:
                wipeout = input(
                    "Found potentially crufty directories:\n"
                    "    {found_cruft}\n"
                    "***We strongly recommend releasing from a fresh git clone!***\n"
                    "Automatically remove these directories and continue? (N/!)".format(
                        found_cruft="\n    ".join(found_cruft)
                    )
                )
            if wipeout == "!":
                for cruft_dir in found_cruft:
                    subprocess.check_output(["rm", "-rfv", cruft_dir])
            else:
                raise Exception(
                    "Bailing: Cowardly refusing to publish with potentially crufty directories "
                    "present! We strongly recommend releasing from a fresh git clone."
                )

        found_pyc_files = []

        for root, _, files in os.walk(git_repo_root()):
            for file_ in files:
                if file_.endswith(".pyc"):
                    found_pyc_files.append(os.path.join(root, file_))

        if found_pyc_files:
            if autoclean:
                wipeout = "!"
            else:
                wipeout = input(
                    "Found {n_files} .pyc files.\n"
                    "We strongly recommend releasing from a fresh git clone!\n"
                    "Automatically remove these files and continue? (N/!)".format(
                        n_files=len(found_pyc_files)
                    )
                )
            if wipeout == "!":
                for file_ in found_pyc_files:
                    os.unlink(file_)
            else:
                raise Exception(
                    "Bailing: Cowardly refusing to publish with .pyc files present! "
                    "We strongly recommend releasing from a fresh git clone."
                )

    def check_directory_structure(self):
        """Check to ensure that the git repo directory structure matches our expectations.

        First ensure that the set of paths under python_modules/ is correct, then the set of paths
        under python_modules/libraries/

        Raises:
            Exception: Raised if there's some difference between the expected modules and the git
                repo.
        """
        expected_python_modules_subdirectories = ["automation", "libraries", "dagster-test"] + [
            module.name for module in self.core_modules
        ]

        unexpected_modules = []
        expected_modules_not_found = []

        module_directories = get_core_module_directories()

        for module_dir in module_directories:
            if module_dir.name not in expected_python_modules_subdirectories:
                unexpected_modules.append(module_dir.path)

        for module_dir_name in expected_python_modules_subdirectories:
            if module_dir_name not in [module_dir.name for module_dir in module_directories]:
                expected_modules_not_found.append(module_dir_name)

        if unexpected_modules or expected_modules_not_found:
            raise Exception(
                "Bailing: something looks wrong. We're either missing modules we expected or modules "
                "are present that we don't know about:\n"
                "{expected_modules_not_found_msg}"
                "{unexpected_modules_msg}".format(
                    expected_modules_not_found_msg=(
                        (
                            "\nDidn't find expected modules:\n    {expected_modules_not_found}"
                        ).format(
                            expected_modules_not_found="\n    ".join(
                                sorted(expected_modules_not_found)
                            )
                        )
                        if expected_modules_not_found
                        else ""
                    ),
                    unexpected_modules_msg=(
                        "\nFound unexpected modules:\n    {unexpected_modules}".format(
                            unexpected_modules="\n    ".join(sorted(unexpected_modules))
                        )
                        if unexpected_modules
                        else ""
                    ),
                )
            )

    def check_all_versions_equal(self):
        """Checks that all versions are equal

        Returns:
            List[dict]: List of dictionaries of version info
        """
        module_versions = self.all_module_versions

        if not all_equal(module_versions.values()):
            click.echo(
                "Warning! Found repository in a bad state. Existing package versions were not "
                "equal:\n{versions}".format(versions=format_module_versions(module_versions))
            )
        return module_versions

    def check_version(self):
        click.echo("Checking that module versions are in lockstep")

        module_version = self.check_all_versions_equal()["dagster"]["__version__"]
        git_tag = get_git_tag()
        assert (
            module_version == git_tag
        ), "Version {version} does not match expected git tag {git_tag}".format(
            version=module_version, git_tag=git_tag
        )

        return module_version

    def check_new_version(self, new_version):
        """Ensure that a new version is valid: greater than or equal to existing published
        versions, and with a pre-release already published.

        Args:
            new_version (str): New version to check

        Raises:
            Exception: An invalid version was provided or a pre-release was not found.

        Returns:
            [type]: [description]
        """
        parsed_version = packaging.version.parse(new_version)
        module_versions = self.check_all_versions_equal()
        errors = {}
        last_version = None
        for module_name, module_version in module_versions.items():
            last_version = module_version
            if packaging.version.parse(module_version["__version__"]) >= parsed_version:
                errors[module_name] = module_version["__version__"]
        if errors:
            raise Exception(
                "Bailing: Found modules with existing versions greater than or equal to the new "
                "version {new_version}:\n{versions}".format(
                    new_version=new_version, versions=format_module_versions(module_versions)
                )
            )

        if not (
            parsed_version.is_prerelease
            or parsed_version.is_postrelease
            or parsed_version.is_devrelease
        ):
            parsed_previous_version = packaging.version.parse(last_version["__version__"])
            if not (parsed_previous_version.release == parsed_version.release):
                should_continue = input(
                    "You appear to be releasing a new version, {new_version}, without having "
                    "previously run a prerelease.\n(Last version found was {previous_version})\n"
                    "Are you sure you know what you're doing? (N/!)".format(
                        new_version=new_version, previous_version=last_version["__version__"]
                    )
                )
                if not should_continue == "!":
                    raise Exception("Bailing! Run a pre-release before continuing.")

    def set_version_info(self, new_version=None, dry_run=True):
        """Updates the version in version.py files for all modules we manage/release.

        Args:
            new_version (str, optional): A new module version. Defaults to None.
            dry_run (bool, optional): Whether this operation should be a dry run. Defaults to True.

        Returns:
            List[dict]: The new versions of all modules.
        """
        versions = []
        for module in self.all_publishable_modules:
            new_version = new_version or module.get_version_info()["__version__"]
            res = module.set_version_info(new_version, dry_run=dry_run)

            versions.append(res)

        assert all_equal(versions)
        return versions[0]

    def commit_new_version(self, new_version, dry_run=True):
        try:
            for module in self.all_publishable_modules:
                cmd = [
                    "git",
                    "add",
                    module.version_file_path,
                ]
                check_output(cmd, dry_run=dry_run)

            cmd = [
                "git",
                "commit",
                "--no-verify",
                "-m",
                "{new_version}".format(new_version=new_version),
            ]
            check_output(cmd, dry_run=dry_run)

        except subprocess.CalledProcessError as exc_info:
            raise Exception(exc_info.output)

    def publish_all(self, dry_run=True):
        for module in self.all_publishable_modules:
            module.publish(dry_run=dry_run)


def get_core_module_directories():
    """List core module directories (not including libraries) under python_modules.

    Returns:
        List(os.DirEntry): List of core module directories
    """
    core_module_root_dir = os.path.join(git_repo_root(), "python_modules")
    module_directories = [
        dir_
        for dir_ in os.scandir(core_module_root_dir)
        if dir_.is_dir() and not dir_.name.startswith(".")
    ]
    return module_directories


def get_library_module_directories():
    """List library module directories under python_modules/libraries.

    Returns:
        List(os.DirEntry): List of core module directories
    """
    library_module_root_dir = os.path.join(git_repo_root(), "python_modules", "libraries")
    library_directories = [
        dir_
        for dir_ in os.scandir(library_module_root_dir)
        if dir_.is_dir() and not dir_.name.startswith(".")
    ]
    return library_directories
