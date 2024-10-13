import click

from automation.graphql.python_client.query import query

CLI_HELP = """This CLI is used for commands related to the Dagster GraphQL client
"""


def create_cli():
    commands = {"query": query}

    @click.group(commands=commands, help=CLI_HELP)
    def group():
        pass

    return group


cli = create_cli()


def main():
    click_cli = click.CommandCollection(sources=[cli], help=CLI_HELP)
    click_cli()


if __name__ == "__main__":
    main()
