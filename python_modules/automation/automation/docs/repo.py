# pylint: disable=print-call
import os
import re
import shutil
import subprocess
import sys

from automation.git import git_commit_updates, git_repo_root
from dagster.utils import mkdir_p


class DagsterRepo:
    """For manipulating a dagster cloned repo."""

    def __init__(self):
        self.base_dir = git_repo_root()

    @property
    def docs_path(self):
        return os.path.join(self.base_dir, "docs")

    @property
    def out_path(self):
        path = os.path.join(self.docs_path, "out")
        mkdir_p(path)
        return path

    def build_docs(self, docs_version):
        """Run docs build"""
        cmd = "NODE_ENV=production VERSION={} make full_docs_build".format(docs_version)
        print("Running build:\n", cmd)
        subprocess.call(cmd, cwd=self.docs_path, shell=True)

    def commit(self, docs_version):
        git_commit_updates(self.base_dir, message="[Docs] {}".format(docs_version))


class DagsterDocsRepo:
    """For manipulating a dagster-docs cloned repo."""

    def __init__(self, docs_dir, should_clone=True):
        self.docs_dir = docs_dir

        # Clone dagster-docs
        if not os.path.exists(docs_dir) and should_clone:
            print("Cloning docs repo...")
            cmd = "git clone git@github.com:dagster-io/dagster-docs.git {}".format(docs_dir)
            subprocess.call(cmd, shell=True)

    def check_new_version_dir(self, docs_version):
        """Checks dagster-docs/x.x.x version folder and ensure it doesn't already exist"""
        new_version_path = os.path.join(self.docs_dir, docs_version)
        if os.path.exists(new_version_path):
            print("Cannot build docs; version folder {} already exists!".format(new_version_path))
            sys.exit(1)

    def remove_existing_docs_files(self):
        """We need to remove files in the base directory of dagster-docs before adding the newly
        built docs files.
        """
        dir_contents = list(next(os.walk(self.docs_dir)))

        # Remove all files
        for filename in dir_contents[2]:
            if filename == "netlify.toml":
                continue

            filepath = os.path.join(self.docs_dir, filename)
            print("Removing {}".format(filepath))
            os.remove(filepath)

        # Also remove subdirectories
        for subdir in dir_contents[1]:
            # Skip git and semver folders
            if re.match(r"^.git|^\d+\.\d+\.\d+", subdir):
                continue

            fname = os.path.join(self.docs_dir, subdir)
            print("Removing {}".format(fname))
            shutil.rmtree(fname)

    def commit(self, docs_version):
        git_commit_updates(self.docs_dir, message="[Docs] {}".format(docs_version))
