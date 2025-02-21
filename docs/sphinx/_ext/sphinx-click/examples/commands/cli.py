# file: cli.py
import click


@click.command()
@click.option('--param', envvar='PARAM', help='A sample option')
@click.option('--another', metavar='[FOO]', help='Another option')
@click.option(
    '--choice',
    help='A sample option with choices',
    type=click.Choice(['Option1', 'Option2']),
)
@click.option(
    '--numeric-choice',
    metavar='<choice>',
    help='A sample option with numeric choices',
    type=click.Choice([1, 2, 3]),
)
@click.option(
    '--flag',
    is_flag=True,
    help='A boolean flag',
)
@click.argument('ARG', envvar='ARG')
def cli(
    param: str,
    another: str,
    choice: str,
    numeric_choice: int,
    flag: bool,
) -> None:
    """A sample command."""
    pass
