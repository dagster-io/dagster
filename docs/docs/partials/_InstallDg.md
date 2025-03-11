Once you have installed `uv`, use it to install `dg`.

<CliInvocationExample contents="uv tool install dagster-dg" />

:::tip

`uv tool install` installs python packages from PyPI into isolated environments and exposes their executables on your shell path. This means the `dg` command should now be available. It will always execute in an isolated environment separate from any project environment.

:::

:::note

If you have a local clone of the `dagster` repo, you can install a local version of `dg` with `uv tool install -e $DAGSTER_GIT_REPO_DIR/python_modules/libraries/dagster-dg`. This will create an isolated environment for `dg` just like the standard `uv tool install`, but the environment will contain an editable installation of `dagster-dg`.

:::