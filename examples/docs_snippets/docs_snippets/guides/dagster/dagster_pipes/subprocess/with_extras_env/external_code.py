# ruff: noqa: T201

import os

from dagster_pipes import PipesContext, open_dagster_pipes


def main():
    # get the Dagster Pipes context
    context = PipesContext.get()
    # get all extras provided by Dagster asset
    print(context.extras)
    # get the value of an extra
    print(context.get_extra("foo"))
    # get env var
    print(os.environ["MY_ENV_VAR_IN_SUBPROCESS"])


if __name__ == "__main__":
    # connect to Dagster Pipes
    with open_dagster_pipes():
        main()
