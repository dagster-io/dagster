"""The greet example taken from the README."""

import click


@click.group()
def greet():
    """A sample command group."""
    pass


@greet.command()
@click.argument('user', envvar='USER')
def hello(user):
    """Greet a user."""
    click.echo('Hello %s' % user)


@greet.command()
def world():
    """Greet the world."""
    click.echo('Hello world!')
