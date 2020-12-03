# `.devcontainer` for [GitHub Codespaces](https://github.com/features/codespaces)

## Status
This is currently a very rudimentary setup. Some manual steps are still needed for initializing a codespace.

## What's included
1. The base container is [`codespaces-linux`](https://github.com/microsoft/vscode-dev-containers/tree/master/containers/codespaces-linux). It comes with a variety of tools preinstalled, including `git`, `nvm`, `yarn`, etc.
2. On top of that, the container also [installs](scripts/install-dependencies.sh):
    - [`arc`](https://secure.phabricator.com/book/phabricator/article/arcanist/)
    - `pyenv` and Python 3.7.4 (as mentioned in the [contributing guide](https://docs.dagster.io/community/contributing))

## Initial Setup
1. Follow the instructions to [create a codespace](https://docs.github.com/en/free-pro-team@latest/github/developing-online-with-codespaces/creating-a-codespace#creating-a-codespace)
2. (Optional) Connect to your codespace in [VS Code](https://docs.github.com/en/free-pro-team@latest/github/developing-online-with-codespaces/using-codespaces-in-visual-studio-code)
3. Follow the manual steps below

## Manual Steps Required for Initial Setup
1. (Only needed if you use Phabricator) [Install Arcanist Credentials](https://secure.phabricator.com/book/phabricator/article/arcanist_quick_start/#install-arcanist-credentials): `arc install-certificate`
2. Create and activate a virtualenv:
```
$ pyenv virtualenv 3.7.4 dagster-3.7.4
$ pyenv activate dagster-3.7.4
```
3. Run `make dev_install` at the root of the repository and follow the [contributing guide](https://docs.dagster.io/community/contributing)
