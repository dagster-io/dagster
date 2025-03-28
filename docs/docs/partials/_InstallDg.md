Next, use `uv` to install `dg`:

<CliInvocationExample contents="uv tool install dagster-dg" />

:::tip

`uv tool install` installs Python packages from PyPI into isolated environments and exposes their executables on your shell path. This means the `dg` command will always execute in an isolated environment separate from any project environment.

:::

:::note

If you have a local clone of the `dagster` repo, you can install a local version of `dg` by running `make install_editable_uv_tools` in the root folder of the repo. This will create an isolated environment for `dg` like the standard `uv tool install`, but the environment will contain an editable installation of `dagster-dg`.

:::
