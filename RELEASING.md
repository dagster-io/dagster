## Versioning guidelines

Dagster versions follow the guidelines in [PEP 440](https://www.python.org/dev/peps/pep-0440/).

To make dependency management easier in the context of a monorepo with many installable projects,
package versions move in lockstep with each other and with git tags.

As the API is still in flux, we aren't following strict semantic versioning rules at this point, but
roughly intend micro versions to reflect a regular release schedule and minor versions to reflect
milestones in the framework's capabilities and the maturity of its internals.

You must have wheel and twine installed.

## Releasing a new version

Our release automation tools are contained in `bin/publish.py`. These tools are smart enough to
guard against some kinds of mistakes, but could and should be smarter. Generally speaking, it's
preferable to invest in these tools rather than to complicate the release process.

**Run a pre-release before releasing a new version**: it's good practice to run the release process
for a pre-release version before releasing a new version, i.e., first for version 0.3.0.pre0, and
then for version 0.3.0 only when you know that the process is going to succeed without issues.
This ensures a clean release history.

_WARNING_: Keep in mind that there is no undo in some of the third-party systems (e.g., PyPI) we use to
release software.

You should also run releases from a clean clone of the repository.

     git clone git@github.com:dagster-io/dagster.git

This is to guard against any issues that might be introduced by local build artifacts.

It's also prudent to release from a fresh virtualenv.

## Before releasing

- You must have PyPI credentials available to twine (see below), and you must be permissioned as a
  maintainer on the projects.
- You must export `SLACK_RELEASE_BOT_TOKEN` with an appropriate value.
- You should also export `PYTHONDONTWRITEBYTECODE=1` to avoid writing any extraneous .pyc files.
- You should have set your git config name and email (used for the Slack post).

### Release checklist

1.  Check that you are on `master`, that there are no local changes or changes on the remote, and
    that you are at the root of the repository.

2.  Make sure that you have installed the release requirements by running
    `pip install -r bin/requirements.txt`.

3.  Check that the current version of the projects is consistent and what you expect by running:

        python bin/publish.py version

4.  Create a new release by running (e.g., for version `0.4.3.pre0`):

        python bin/publish.py release 0.4.3.pre0

5.  Check that the new version has been created successfully by again running:

        python bin/publish.py version

6.  Push the new version to the remote. If something goes wrong at this stage, don't panic! See
    "recovering from drift against remote" below.

        git push && git push origin 0.4.3.pre0

7.  Publish the new version to PyPI. If something goes wrong during this stage, you will probably
    have to roll forwards to a new release, since there is no way to delete files from PyPI.

        python bin/publish.py publish

8.  Check that the PyPI versions are as you expect. Note that PYPI automatically changes pre0 to
    rc0.

        python bin/publish.py audit 0.4.3rc0

9.  Post release notes in Dagster Slack in #general, and copy the same release notes to the
    [Github releases page](https://github.com/dagster-io/dagster/releases).

### PyPI credentials

Credentials must be available to twine in order to publish to PyPI. The best way to do this is
with a `~/.pypirc` file in the following format:

    [distutils]
    index-servers = pypi

    [pypi]
    repository: https://upload.pypi.org/legacy/
    username: <username>
    password: <password>

### Recovering from drift against remote

So you pushed a new version and got something like this:

        15:52 $ git push && git push origin 0.6.5.pre0
        To github.com:dagster-io/dagster.git
        ! [rejected]          master -> master (non-fast-forward)
        error: failed to push some refs to 'git@github.com:dagster-io/dagster.git'
        hint: Updates were rejected because the tip of your current branch is behind
        hint: its remote counterpart. Integrate the remote changes (e.g.
        hint: 'git pull ...') before pushing again.

Don't panic, you can recover your previous state and continue with a clean version.

First, you'll want to `git reset --hard` to the commit before your new version.

Then, you'll need to delete the tag you created -- `git tag -d 0.6.5.pre0`, for example.

Now you are clear to `git pull` and proceed from step 1 above.
