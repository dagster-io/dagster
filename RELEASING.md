## Versioning guidelines

Dagster versions follow the guidelines in [PEP 440](https://www.python.org/dev/peps/pep-0440//).

To make dependency management easier in the context of a monorepo with many installable projects,
package versions move in lockstep with each other and with git tags. 

As the API is still in flux, we aren't following strict semantic versioning rules at this point, but roughly
intend micro versions to reflect a regular release schedule and minor versions to reflect
milestones in the framework's capability.

Breaking API changes should be recorded in `CHANGELOG.rst`.

You must have wheel and twine installed.

## Releasing a new version

Our release automation tools are contained in `bin/publish.py`. These tools are smart enough to
guard against some kinds of mistakes, but could and should be smarter. Generally speaking, it's
preferable to invest in these tools rather than to complicate the release process.

1. Check that you are on `master`, that there are no local changes or changes on the remote, and
   that you are at the root of the repository.

2. Check that the current version of the projects is consistent and what you expect by running:

    python bin/publish.py version

3. Create a new release by running (e.g., for version 0.3.0):

    python bin/publish.py release 0.3.0

4. Check that the new version has been created successfully by again running:

    python bin/publish.py version

5. Push the new version to the remote. The new version tag will trigger a ReadTheDocs build.

    git push && git push --tags

6. Publish the new version to PyPI. Note that you must have PyPI credentials available to twine
   (see below), and you must be permissioned as a maintainer on the projects.

    python bin/publish.py publish

7. Manually switch the default ReadTheDocs version to the newly built docs:
   [https://readthedocs.org/dashboard/dagster/versions/](https://readthedocs.org/dashboard/dagster/versions/)


### PyPI credentials

Credentials must be available to twine in order to publish to PyPI. The best way to do this is
with a `~/.pypirc` file in the following format:

    [distutils]
    index-servers = pypi

    [pypi]
    repository: https://upload.pypi.org/legacy/
    username: <username>
    password: <password>
