"""The greet example taken from the README."""

import click
import fake_dependency  # Used to test that mocking works


@click.group()
def greet():
    """A sample command group."""
    fake_dependency.do_stuff("hello!")


@greet.command()
@click.argument('user', envvar='USER')
def hello(user):
    """Greet a user."""
    click.echo('Hello %s' % user)


@greet.command()
def world():
    """Greet the world."""
    click.echo('Hello world!')
