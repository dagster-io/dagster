import os
import re
import subprocess

import six

from .utils import check_output


def git_check_status():
    changes = six.ensure_str(subprocess.check_output(["git", "status", "--porcelain"]))
    if changes != "":
        raise Exception(
            "Bailing: Cannot publish with changes present in git repo:\n{changes}".format(
                changes=changes
            )
        )


def git_user():
    return six.ensure_str(
        subprocess.check_output(["git", "config", "--get", "user.name"]).decode("utf-8").strip()
    )


def git_repo_root():
    return six.ensure_str(subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).strip())


def git_push(tag=None, dry_run=True, cwd=None):
    github_token = os.getenv("GITHUB_TOKEN")
    github_username = os.getenv("GITHUB_USERNAME")
    if github_token and github_username:
        if tag:
            check_output(
                [
                    "git",
                    "push",
                    "https://{github_username}:{github_token}@github.com/dagster-io/dagster.git".format(
                        github_username=github_username, github_token=github_token
                    ),
                    tag,
                ],
                dry_run=dry_run,
                cwd=cwd,
            )
        check_output(
            [
                "git",
                "push",
                "https://{github_username}:{github_token}@github.com/dagster-io/dagster.git".format(
                    github_username=github_username, github_token=github_token
                ),
            ],
            dry_run=dry_run,
            cwd=cwd,
        )
    else:
        if tag:
            check_output(["git", "push", "origin", tag], dry_run=dry_run, cwd=cwd)
        check_output(["git", "push"], dry_run=dry_run, cwd=cwd)


def get_git_tag():
    try:
        git_tag = str(
            subprocess.check_output(
                ["git", "describe", "--exact-match", "--abbrev=0"], stderr=subprocess.STDOUT
            )
        ).strip("'b\\n")
    except subprocess.CalledProcessError as exc_info:
        match = re.search(
            "fatal: no tag exactly matches '(?P<commit>[a-z0-9]+)'", str(exc_info.output)
        )
        if match:
            raise Exception(
                "Bailing: there is no git tag for the current commit, {commit}".format(
                    commit=match.group("commit")
                )
            )
        raise Exception(str(exc_info.output))

    return git_tag


def get_most_recent_git_tag():
    try:
        git_tag = str(
            subprocess.check_output(["git", "describe", "--abbrev=0"], stderr=subprocess.STDOUT)
        ).strip("'b\\n")
    except subprocess.CalledProcessError as exc_info:
        raise Exception(str(exc_info.output))
    return git_tag


def get_git_repo_branch(cwd=None):
    git_branch = six.ensure_str(
        subprocess.check_output(["git", "branch", "--show-current"], cwd=cwd)
    ).strip()
    return git_branch


def set_git_tag(tag, signed=False, dry_run=True):
    try:
        if signed:
            if not dry_run:
                subprocess.check_output(
                    ["git", "tag", "-s", "-m", tag, tag], stderr=subprocess.STDOUT
                )
        else:
            if not dry_run:
                subprocess.check_output(
                    ["git", "tag", "-a", "-m", tag, tag], stderr=subprocess.STDOUT
                )

    except subprocess.CalledProcessError as exc_info:
        match = re.search("error: gpg failed to sign the data", str(exc_info.output))
        if match:
            raise Exception(
                "Bailing: cannot sign tag. You may find "
                "https://stackoverflow.com/q/39494631/324449 helpful. Original error "
                "output:\n{output}".format(output=str(exc_info.output))
            )

        match = re.search(
            r"fatal: tag \'(?P<tag>[\.a-z0-9]+)\' already exists", str(exc_info.output)
        )
        if match:
            raise Exception(
                "Bailing: cannot release version tag {tag}: already exists".format(
                    tag=match.group("tag")
                )
            )
        raise Exception(str(exc_info.output))

    return tag


def git_commit_updates(repo_dir, message):
    cmds = [
        "git add -A",
        'git commit -m "{}"'.format(message),
    ]

    print(  # pylint: disable=print-call
        "Committing to {} with message {}".format(repo_dir, message)
    )
    for cmd in cmds:
        subprocess.call(cmd, cwd=repo_dir, shell=True)
