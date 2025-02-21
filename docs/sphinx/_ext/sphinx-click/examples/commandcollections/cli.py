# file: cli.py
import click


main = click.Group(
    name='Principal Commands',
    help=(
        "Principal commands that are used in ``cli``.\n\n"
        "The section name and description are obtained using the name and "
        "description of the group passed as sources for |CommandCollection|_."
    ),
)


@main.command(help='CMD 1')
def cmd1() -> None:
    print('call cmd 1')


helpers = click.Group(
    name='Helper Commands',
    help="Helper commands for ``cli``.",
)


@helpers.command()
def cmd2() -> None:
    "Helper command that has no option."
    pass


@helpers.command()
@click.option('--user', type=str)
def cmd3(user: str) -> None:
    "Helper command with an option."
    pass


cli = click.CommandCollection(
    name='cli',
    sources=[main, helpers],
    help='Some general info on ``cli``.',
)
