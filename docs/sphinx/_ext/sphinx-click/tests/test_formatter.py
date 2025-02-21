import textwrap
import unittest

import click
from sphinx_click import ext

CLICK_VERSION = tuple(int(x) for x in click.__version__.split('.')[0:2])


class CommandTestCase(unittest.TestCase):
    """Validate basic ``click.Command`` instances."""

    maxDiff = None

    def test_no_parameters(self):
        """Validate a `click.Command` with no parameters.

        This exercises the code paths for a command with *no* arguments, *no*
        options and *no* environment variables.
        """

        @click.command()
        def foobar():
            """A sample command."""
            pass

        ctx = click.Context(foobar, info_name='foobar')
        output = list(ext._format_command(ctx, nested='short'))

        self.assertEqual(
            textwrap.dedent(
                """
        A sample command.

        .. program:: foobar
        .. code-block:: shell

            foobar [OPTIONS]
        """
            ).lstrip(),
            '\n'.join(output),
        )

    def test_basic_parameters(self):
        """Validate a combination of parameters.

        This exercises the code paths for a command with arguments, options and
        environment variables.
        """

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
        def foobar(bar):
            """A sample command."""
            pass

        ctx = click.Context(foobar, info_name='foobar')
        output = list(ext._format_command(ctx, nested='short'))

        self.assertEqual(
            textwrap.dedent(
                """
        A sample command.

        .. program:: foobar
        .. code-block:: shell

            foobar [OPTIONS] ARG

        .. rubric:: Options

        .. option:: --param <param>

            A sample option

        .. option:: --another <FOO>

            Another option

        .. option:: --choice <choice>

            A sample option with choices

            :options: Option1 | Option2

        .. option:: --numeric-choice <choice>

            A sample option with numeric choices

            :options: 1 | 2 | 3

        .. option:: --flag

            A boolean flag

        .. rubric:: Arguments

        .. option:: ARG

            Required argument

        .. rubric:: Environment variables

        .. _foobar-param-PARAM:

        .. envvar:: PARAM
           :noindex:

            Provide a default for :option:`--param`

        .. _foobar-arg-ARG:

        .. envvar:: ARG
           :noindex:

            Provide a default for :option:`ARG`
        """
            ).lstrip(),
            '\n'.join(output),
        )

    def test_help_epilog(self):
        """Validate formatting of explicit help and epilog strings."""

        @click.command(help='A sample command.', epilog='A sample epilog.')
        @click.option('--param', help='A sample option')
        def foobar(bar):
            pass

        ctx = click.Context(foobar, info_name='foobar')
        output = list(ext._format_command(ctx, nested='short'))

        self.assertEqual(
            textwrap.dedent(
                """
        A sample command.

        .. program:: foobar
        .. code-block:: shell

            foobar [OPTIONS]

        .. rubric:: Options

        .. option:: --param <param>

            A sample option

        A sample epilog.
        """
            ).lstrip(),
            '\n'.join(output),
        )

    def test_help_argument(self):
        """Validate a help text for arguments.

        While click only provides the help attribute for options, but not for arguments,
        it allows customization with subclasses.
        """

        class CustomArgument(click.Argument):
            def __init__(self, *args, help=None, **kwargs):
                super().__init__(*args, **kwargs)
                self.help = help

        @click.command()
        @click.option('--option', help='A sample option')
        @click.argument('ARG', help='A sample argument', cls=CustomArgument)
        @click.argument('ARG_NO_HELP', cls=CustomArgument)
        def foobar(bar):
            """A sample command."""
            pass

        ctx = click.Context(foobar, info_name='foobar')
        output = list(ext._format_command(ctx, nested='short'))

        self.assertEqual(
            textwrap.dedent(
                """
        A sample command.

        .. program:: foobar
        .. code-block:: shell

            foobar [OPTIONS] ARG ARG_NO_HELP

        .. rubric:: Options

        .. option:: --option <option>

            A sample option

        .. rubric:: Arguments

        .. option:: ARG

            Required argument

            A sample argument


        .. option:: ARG_NO_HELP

            Required argument
        """
            ).lstrip(),
            '\n'.join(output),
        )

    def test_defaults(self):
        """Validate formatting of user documented defaults."""

        @click.command()
        @click.option('--num-param', type=int, default=42, show_default=True)
        @click.option(
            '--param',
            default=lambda: None,
            show_default='Something computed at runtime',
        )
        @click.option(
            '--group',
            default=[('foo', 'bar')],
            nargs=2,
            type=click.Tuple([str, str]),
            multiple=True,
            show_default=True,
        )
        @click.option(
            '--only-show-default',
            show_default="Some default computed at runtime!",
        )
        @click.option('--string-default', default="abc", show_default=True)
        @click.option('--empty-string-default', default="", show_default=True)
        def foobar(bar):
            """A sample command."""
            pass

        ctx = click.Context(foobar, info_name='foobar')
        output = list(ext._format_command(ctx, nested='short'))

        self.assertEqual(
            textwrap.dedent(
                """
        A sample command.

        .. program:: foobar
        .. code-block:: shell

            foobar [OPTIONS]

        .. rubric:: Options

        .. option:: --num-param <num_param>

            :default: ``42``

        .. option:: --param <param>

            :default: ``'Something computed at runtime'``

        .. option:: --group <group>

            :default: ``('foo', 'bar')``

        .. option:: --only-show-default <only_show_default>

            :default: ``'Some default computed at runtime!'``

        .. option:: --string-default <string_default>

            :default: ``'abc'``

        .. option:: --empty-string-default <empty_string_default>

            :default: ``''``
        """
            ).lstrip(),
            '\n'.join(output),
        )

    def test_show_default(self):
        """Validate formatting of show_default via context_settings."""

        @click.command(context_settings={"show_default": True})
        @click.option('--no-set', default=0)
        @click.option('--set-false', default=0, show_default=False)
        def foobar():
            """A sample command."""
            pass

        ctx = click.Context(foobar, info_name='foobar', show_default=True)
        output = list(ext._format_command(ctx, nested='short'))
        self.assertEqual(
            textwrap.dedent(
                """
        A sample command.

        .. program:: foobar
        .. code-block:: shell

            foobar [OPTIONS]

        .. rubric:: Options

        .. option:: --no-set <no_set>

            :default: ``0``

        .. option:: --set-false <set_false>
        """
            ).lstrip(),
            '\n'.join(output),
        )

    def test_hidden(self):
        """Validate a `click.Command` with the `hidden` flag."""

        @click.command(hidden=True)
        def foobar():
            """A sample command."""
            pass

        ctx = click.Context(foobar, info_name='foobar')
        output = list(ext._format_command(ctx, nested='short'))

        self.assertEqual('', '\n'.join(output))

    def test_titles(self):
        """Validate a `click.Command` with nested titles."""

        @click.command()
        @click.option('--name', help='Name to say hello to.', required=True, type=str)
        def hello(name):
            """Prints hello to name given.

            Examples
            --------

            .. code:: bash

                my_cli hello --name "Jack"
            """

        ctx = click.Context(hello, info_name='hello')
        output = list(ext._format_command(ctx, nested='short'))

        self.assertEqual(
            textwrap.dedent(
                """
        Prints hello to name given.

        Examples
        --------

        .. code:: bash

            my_cli hello --name "Jack"

        .. program:: hello
        .. code-block:: shell

            hello [OPTIONS]

        .. rubric:: Options

        .. option:: --name <name>

            **Required** Name to say hello to.
        """
            ).lstrip(),
            '\n'.join(output),
        )

    def test_ansi_escape_sequences(self):
        """Validate that ANSI escape sequences are stripped."""

        @click.command(epilog='\033[31mA sample epilog.\033[0m')
        @click.option(
            '--name',
            help='Name to say \033[94mhello\033[0m to.',
            required=True,
            type=str,
        )
        @click.option(
            '--choice',
            help='A sample option with choices',
            type=click.Choice(['\033[94mOption1\033[0m', '\033[94mOption2\033[0m']),
        )
        @click.option(
            '--param',
            default=lambda: None,
            show_default='Something computed at \033[94mruntime\033[0m',
        )
        def foobar():
            """A sample command with **sparkles**.

            We've got \033[31mred text\033[0m, \033[104mblue backgrounds\033[0m, a
            dash of \033[1mbold\033[0m and even some \033[4munderlined words\033[0m.
            """
            pass

        ctx = click.Context(foobar, info_name='foobar')
        output = list(ext._format_command(ctx, nested='short'))

        self.assertEqual(
            textwrap.dedent(
                """
        A sample command with **sparkles**.

        We've got red text, blue backgrounds, a
        dash of bold and even some underlined words.

        .. program:: foobar
        .. code-block:: shell

            foobar [OPTIONS]

        .. rubric:: Options

        .. option:: --name <name>

            **Required** Name to say hello to.

        .. option:: --choice <choice>

            A sample option with choices

            :options: Option1 | Option2

        .. option:: --param <param>

            :default: ``'Something computed at runtime'``

        A sample epilog.
        """
            ).lstrip(),
            '\n'.join(output),
        )

    @unittest.skipIf(
        CLICK_VERSION < (8, 1), 'Click < 8.1.0 stores the modified help string'
    )
    def test_no_truncation(self):
        r"""Validate behavior when a \f character is present.

        https://click.palletsprojects.com/en/8.1.x/documentation/#truncating-help-texts
        """

        @click.command()
        def cli():
            """First paragraph.

            This is a very long second
            paragraph and not correctly
            wrapped but it will be rewrapped.
            \f

            :param click.core.Context ctx: Click context.
            """
            pass

        ctx = click.Context(cli, info_name='cli')
        output = list(ext._format_command(ctx, nested='short'))

        # note that we have an extra newline because we're using
        # docutils.statemachine.string2lines under the hood, which is
        # converting the form feed to a newline
        self.assertEqual(
            textwrap.dedent(
                """
        First paragraph.

        This is a very long second
        paragraph and not correctly
        wrapped but it will be rewrapped.


        :param click.core.Context ctx: Click context.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS]
        """
            ).lstrip(),
            '\n'.join(output),
        )

    def test_no_line_wrapping(self):
        r"""Validate behavior when a \b character is present.

        https://click.palletsprojects.com/en/8.1.x/documentation/#preventing-rewrapping
        """

        @click.command(
            epilog="""
An epilog containing pre-wrapped text.

\b
This is
a paragraph
without rewrapping.

And this is a paragraph
that will be rewrapped again.
"""
        )
        @click.option(
            '--param',
            help="""An option containing pre-wrapped text.

            \b
            This is
            a paragraph
            without rewrapping.

            And this is a paragraph
            that will be rewrapped again.
            """,
        )
        def cli():
            """A command containing pre-wrapped text.

            \b
            This is
            a paragraph
            without rewrapping.

            And this is a paragraph
            that will be rewrapped again.
            """
            pass

        ctx = click.Context(cli, info_name='cli')
        output = list(ext._format_command(ctx, nested='short'))

        self.assertEqual(
            textwrap.dedent(
                """
        A command containing pre-wrapped text.

        | This is
        | a paragraph
        | without rewrapping.

        And this is a paragraph
        that will be rewrapped again.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS]

        .. rubric:: Options

        .. option:: --param <param>

            An option containing pre-wrapped text.

            | This is
            | a paragraph
            | without rewrapping.

            And this is a paragraph
            that will be rewrapped again.

        An epilog containing pre-wrapped text.

        | This is
        | a paragraph
        | without rewrapping.

        And this is a paragraph
        that will be rewrapped again.
        """
            ).lstrip(),
            '\n'.join(output),
        )


class GroupTestCase(unittest.TestCase):
    """Validate basic ``click.Group`` instances."""

    maxDiff = None

    def test_no_parameters(self):
        """Validate a `click.Group` with no parameters.

        This exercises the code paths for a group with *no* arguments, *no*
        options and *no* environment variables.
        """

        @click.group()
        def cli():
            """A sample command group."""
            pass

        ctx = click.Context(cli, info_name='cli')
        output = list(ext._format_command(ctx, nested='short'))

        self.assertEqual(
            textwrap.dedent(
                """
        A sample command group.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...
        """
            ).lstrip(),
            '\n'.join(output),
        )

    def test_basic_parameters(self):
        """Validate a combination of parameters.

        This exercises the code paths for a group with arguments, options and
        environment variables.
        """

        @click.group()
        @click.option('--param', envvar='PARAM', help='A sample option')
        @click.argument('ARG', envvar='ARG')
        def cli():
            """A sample command group."""
            pass

        ctx = click.Context(cli, info_name='cli')
        output = list(ext._format_command(ctx, nested='short'))

        self.assertEqual(
            textwrap.dedent(
                """
        A sample command group.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] ARG COMMAND [ARGS]...

        .. rubric:: Options

        .. option:: --param <param>

            A sample option

        .. rubric:: Arguments

        .. option:: ARG

            Required argument

        .. rubric:: Environment variables

        .. _cli-param-PARAM:

        .. envvar:: PARAM
           :noindex:

            Provide a default for :option:`--param`

        .. _cli-arg-ARG:

        .. envvar:: ARG
           :noindex:

            Provide a default for :option:`ARG`
        """
            ).lstrip(),
            '\n'.join(output),
        )


class NestedCommandsTestCase(unittest.TestCase):
    """Validate ``click.Command`` instances inside ``click.Group`` instances."""

    maxDiff = None

    @staticmethod
    def _get_ctx():
        @click.group()
        def cli():
            """A sample command group."""
            pass

        @cli.command()
        def hello():
            """A sample command."""
            pass

        return click.Context(cli, info_name='cli')

    def test_nested_short(self):
        """Validate a nested command with 'nested' of 'short' (default).

        We should list minimal help texts for sub-commands since they're not
        being handled separately.
        """

        ctx = self._get_ctx()
        output = list(ext._format_command(ctx, nested='short'))

        self.assertEqual(
            textwrap.dedent(
                """
        A sample command group.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...

        .. rubric:: Commands

        .. object:: hello

            A sample command.
        """
            ).lstrip(),
            '\n'.join(output),
        )

    def test_nested_full(self):
        """Validate a nested command with 'nested' of 'full'.

        We should not list sub-commands since they're being handled separately.
        """

        ctx = self._get_ctx()
        output = list(ext._format_command(ctx, nested='full'))

        self.assertEqual(
            textwrap.dedent(
                """
        A sample command group.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...
        """
            ).lstrip(),
            '\n'.join(output),
        )

    def test_nested_none(self):
        """Validate a nested command with 'nested' of 'none'.

        We should not list sub-commands.
        """

        ctx = self._get_ctx()
        output = list(ext._format_command(ctx, nested='none'))

        self.assertEqual(
            textwrap.dedent(
                """
        A sample command group.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...
        """
            ).lstrip(),
            '\n'.join(output),
        )


class CommandFilterTestCase(unittest.TestCase):
    """Validate filtering of commands."""

    maxDiff = None

    @staticmethod
    def _get_ctx():
        @click.group()
        def cli():
            """A sample command group."""

        @cli.command()
        def hello():
            """A sample command."""

        @cli.command()
        def world():
            """A world command."""

        return click.Context(cli, info_name='cli')

    def test_no_commands(self):
        """Validate an empty command group."""

        ctx = self._get_ctx()
        output = list(ext._format_command(ctx, nested='short', commands=[]))

        self.assertEqual(
            textwrap.dedent(
                """
        A sample command group.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...
        """
            ).lstrip(),
            '\n'.join(output),
        )

    def test_order_of_commands(self):
        """Validate the order of commands."""

        ctx = self._get_ctx()
        output = list(
            ext._format_command(ctx, nested='short', commands=['world', 'hello'])
        )

        self.assertEqual(
            textwrap.dedent(
                """
        A sample command group.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...

        .. rubric:: Commands

        .. object:: world

            A world command.

        .. object:: hello

            A sample command.
        """
            ).lstrip(),
            '\n'.join(output),
        )


class CustomMultiCommandTestCase(unittest.TestCase):
    """Validate ``click.MultiCommand`` instances."""

    maxDiff = None

    def test_basics(self):
        """Validate a custom ``click.MultiCommand`` with no parameters.

        This exercises the code paths to extract commands correctly from these
        commands.
        """

        @click.command()
        def hello():
            """A sample command."""

        @click.command()
        def world():
            """A world command."""

        class MyCLI(click.MultiCommand):
            _command_mapping = {
                'hello': hello,
                'world': world,
            }

            def list_commands(self, ctx):
                return ['hello', 'world']

            def get_command(self, ctx, name):
                return self._command_mapping[name]

        cli = MyCLI(help='A sample custom multicommand.')
        ctx = click.Context(cli, info_name='cli')
        output = list(ext._format_command(ctx, nested='short'))

        self.assertEqual(
            textwrap.dedent(
                """
        A sample custom multicommand.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...

        .. rubric:: Commands

        .. object:: hello

            A sample command.

        .. object:: world

            A world command.
        """
            ).lstrip(),
            '\n'.join(output),
        )

    def test_hidden(self):
        """Ensure 'hidden' subcommands are not shown."""

        @click.command()
        def hello():
            """A sample command."""

        @click.command()
        def world():
            """A world command."""

        @click.command(hidden=True)
        def hidden():
            """A hidden command."""

        class MyCLI(click.MultiCommand):
            _command_mapping = {
                'hello': hello,
                'world': world,
                'hidden': hidden,
            }

            def list_commands(self, ctx):
                return ['hello', 'world', 'hidden']

            def get_command(self, ctx, name):
                return self._command_mapping[name]

        cli = MyCLI(help='A sample custom multicommand.')
        ctx = click.Context(cli, info_name='cli')
        output = list(ext._format_command(ctx, nested='short'))

        # Note that we do NOT expect this to show the 'hidden' command
        self.assertEqual(
            textwrap.dedent(
                """
        A sample custom multicommand.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...

        .. rubric:: Commands

        .. object:: hello

            A sample command.

        .. object:: world

            A world command.
        """
            ).lstrip(),
            '\n'.join(output),
        )


class CommandCollectionTestCase(unittest.TestCase):
    """Validate ``click.CommandCollection`` instances."""

    maxDiff = None

    def test_basics(self):
        "Validate a ``click.CommandCollection`` with grouped outputs."

        @click.group()
        def grp1():
            """A first group."""
            pass

        @grp1.command()
        def hello():
            """A hello command."""

        @click.group()
        def grp2():
            """A second group."""
            pass

        @grp2.command()
        def world():
            """A world command."""

        cli = click.CommandCollection(
            name='cli', sources=[grp1, grp2], help='A simple CommandCollection.'
        )
        ctx = click.Context(cli, info_name='cli')
        output = list(ext._format_command(ctx, nested='full'))

        self.assertEqual(
            textwrap.dedent(
                """
        A simple CommandCollection.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...
        """
            ).lstrip(),
            '\n'.join(output),
        )

        output = list(ext._format_command(ctx, nested='short'))

        self.assertEqual(
            textwrap.dedent(
                """
        A simple CommandCollection.

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS] COMMAND [ARGS]...

        .. rubric:: Commands

        .. object:: hello

            A hello command.

        .. object:: world

            A world command.
        """
            ).lstrip(),
            '\n'.join(output),
        )


class AutoEnvvarPrefixTestCase(unittest.TestCase):
    """Validate ``click auto_envvar_prefix``-setup instances."""

    maxDiff = None

    def test_basics(self):
        """Validate a click application with ``auto_envvar_prefix`` option enabled."""

        @click.command(
            context_settings={"auto_envvar_prefix": "PREFIX"},
        )
        @click.option('--param', help='Help for param')
        @click.option('--other-param', help='Help for other-param')
        @click.option(
            '--param-with-explicit-envvar',
            help='Help for param-with-explicit-envvar',
            envvar="EXPLICIT_ENVVAR",
        )
        def cli_with_auto_envvars():
            """A simple CLI with auto-env vars ."""

        cli = cli_with_auto_envvars
        ctx = click.Context(cli, info_name='cli', auto_envvar_prefix="PREFIX")
        output = list(ext._format_command(ctx, nested='full'))

        self.assertEqual(
            textwrap.dedent(
                """
        A simple CLI with auto-env vars .

        .. program:: cli
        .. code-block:: shell

            cli [OPTIONS]

        .. rubric:: Options

        .. option:: --param <param>

            Help for param

        .. option:: --other-param <other_param>

            Help for other-param

        .. option:: --param-with-explicit-envvar <param_with_explicit_envvar>

            Help for param-with-explicit-envvar

        .. rubric:: Environment variables

        .. _cli-param-PREFIX_PARAM:

        .. envvar:: PREFIX_PARAM
           :noindex:

            Provide a default for :option:`--param`

        .. _cli-other_param-PREFIX_OTHER_PARAM:

        .. envvar:: PREFIX_OTHER_PARAM
           :noindex:

            Provide a default for :option:`--other-param`

        .. _cli-param_with_explicit_envvar-EXPLICIT_ENVVAR:

        .. envvar:: EXPLICIT_ENVVAR
           :noindex:

            Provide a default for :option:`--param-with-explicit-envvar`
        """
            ).lstrip(),
            '\n'.join(output),
        )
