import inspect
import functools
import re
import traceback
import typing as ty
import warnings

try:
    import asyncclick as click
except ImportError:
    import click
import click.core
from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst import directives
from docutils import statemachine
from sphinx import application
from sphinx.util import logging
from sphinx.util import nodes as sphinx_nodes
from sphinx.ext.autodoc import mock

LOG = logging.getLogger(__name__)

NESTED_FULL = 'full'
NESTED_SHORT = 'short'
NESTED_NONE = 'none'
NestedT = ty.Literal['full', 'short', 'none', None]

ANSI_ESC_SEQ_RE = re.compile(r'\x1B\[\d+(;\d+){0,2}m', flags=re.MULTILINE)

_T_Formatter = ty.Callable[[click.Context], ty.Generator[str, None, None]]


def _process_lines(event_name: str) -> ty.Callable[[_T_Formatter], _T_Formatter]:
    def decorator(func: _T_Formatter) -> _T_Formatter:
        @functools.wraps(func)
        def process_lines(ctx: click.Context) -> ty.Generator[str, None, None]:
            lines = list(func(ctx))
            if "sphinx-click-env" in ctx.meta:
                ctx.meta["sphinx-click-env"].app.events.emit(event_name, ctx, lines)
            for line in lines:
                yield line

        return process_lines

    return decorator


def _indent(text: str, level: int = 1) -> str:
    prefix = ' ' * (4 * level)

    def prefixed_lines() -> ty.Generator[str, None, None]:
        for line in text.splitlines(True):
            yield (prefix + line if line.strip() else line)

    return ''.join(prefixed_lines())


def _get_usage(ctx: click.Context) -> str:
    """Alternative, non-prefixed version of 'get_usage'."""
    formatter = ctx.make_formatter()
    pieces = ctx.command.collect_usage_pieces(ctx)
    formatter.write_usage(ctx.command_path, ' '.join(pieces), prefix='')
    return formatter.getvalue().rstrip('\n')  # type: ignore


def _get_help_record(ctx: click.Context, opt: click.core.Option) -> ty.Tuple[str, str]:
    """Re-implementation of click.Opt.get_help_record.

    The variant of 'get_help_record' found in Click makes uses of slashes to
    separate multiple opts, and formats option arguments using upper case. This
    is not compatible with Sphinx's 'option' directive, which expects
    comma-separated opts and option arguments surrounded by angle brackets [1].

    [1] http://www.sphinx-doc.org/en/stable/domains.html#directive-option
    """

    def _write_opts(opts: ty.List[str]) -> str:
        rv, _ = click.formatting.join_options(opts)
        if not opt.is_flag and not opt.count:
            name = opt.name
            if opt.metavar:
                name = opt.metavar.lstrip('<[{($').rstrip('>]})$')
            rv += ' <{}>'.format(name)
        return rv  # type: ignore

    rv = [_write_opts(opt.opts)]
    if opt.secondary_opts:
        rv.append(_write_opts(opt.secondary_opts))

    out = []
    if opt.help:
        if opt.required:
            out.append('**Required** %s' % opt.help)
        else:
            out.append(opt.help)
    else:
        if opt.required:
            out.append('**Required**')

    extras = []

    if opt.show_default is not None:
        show_default = opt.show_default
    else:
        show_default = ctx.show_default

    if isinstance(show_default, str):
        # Starting from Click 7.0 show_default can be a string. This is
        # mostly useful when the default is not a constant and
        # documentation thus needs a manually written string.
        extras.append(':default: ``%r``' % ANSI_ESC_SEQ_RE.sub('', show_default))
    elif show_default and opt.default is not None:
        extras.append(
            ':default: ``%s``'
            % (
                ', '.join(repr(d) for d in opt.default)
                if isinstance(opt.default, (list, tuple))
                else repr(opt.default)
            )
        )

    if isinstance(opt.type, click.Choice):
        extras.append(':options: %s' % ' | '.join(str(x) for x in opt.type.choices))

    if extras:
        if out:
            out.append('')

        out.extend(extras)

    return ', '.join(rv), '\n'.join(out)


def _format_help(help_string: str) -> ty.Generator[str, None, None]:
    help_string = inspect.cleandoc(ANSI_ESC_SEQ_RE.sub('', help_string))

    bar_enabled = False
    for line in statemachine.string2lines(
        help_string, tab_width=4, convert_whitespace=True
    ):
        if line == '\b':
            bar_enabled = True
            continue
        if line == '':
            bar_enabled = False
        line = '| ' + line if bar_enabled else line
        yield line
    yield ''


@_process_lines("sphinx-click-process-description")
def _format_description(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format the description for a given `click.Command`.

    We parse this as reStructuredText, allowing users to embed rich
    information in their help messages if they so choose.
    """
    help_string = ctx.command.help or ctx.command.short_help
    if help_string:
        yield from _format_help(help_string)


@_process_lines("sphinx-click-process-usage")
def _format_usage(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format the usage for a `click.Command`."""
    yield '.. code-block:: shell'
    yield ''
    for line in _get_usage(ctx).splitlines():
        yield _indent(line)
    yield ''


def _format_option(
    ctx: click.Context, opt: click.core.Option
) -> ty.Generator[str, None, None]:
    """Format the output for a `click.core.Option`."""
    opt_help = _get_help_record(ctx, opt)

    yield '.. option:: {}'.format(opt_help[0])
    if opt_help[1]:
        yield ''
        bar_enabled = False
        for line in statemachine.string2lines(
            ANSI_ESC_SEQ_RE.sub('', opt_help[1]), tab_width=4, convert_whitespace=True
        ):
            if line == '\b':
                bar_enabled = True
                continue
            if line == '':
                bar_enabled = False
            line = '| ' + line if bar_enabled else line
            yield _indent(line)


@_process_lines("sphinx-click-process-options")
def _format_options(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format all `click.Option` for a `click.Command`."""
    # the hidden attribute is part of click 7.x only hence use of getattr
    params = [
        param
        for param in ctx.command.params
        if isinstance(param, click.core.Option) and not getattr(param, 'hidden', False)
    ]

    for param in params:
        for line in _format_option(ctx, param):
            yield line
        yield ''


def _format_argument(arg: click.Argument) -> ty.Generator[str, None, None]:
    """Format the output of a `click.Argument`."""
    yield '.. option:: {}'.format(arg.human_readable_name)
    yield ''
    yield _indent(
        '{} argument{}'.format(
            'Required' if arg.required else 'Optional', '(s)' if arg.nargs != 1 else ''
        )
    )
    # Subclasses of click.Argument may add a `help` attribute (like typer.main.TyperArgument)
    help = getattr(arg, 'help', None)
    if help:
        yield ''
        help_string = ANSI_ESC_SEQ_RE.sub('', help)
        for line in _format_help(help_string):
            yield _indent(line)


@_process_lines("sphinx-click-process-arguments")
def _format_arguments(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format all `click.Argument` for a `click.Command`."""
    params = [x for x in ctx.command.params if isinstance(x, click.Argument)]

    for param in params:
        for line in _format_argument(param):
            yield line
        yield ''


def _format_envvar(
    param: ty.Union[click.core.Option, click.Argument],
) -> ty.Generator[str, None, None]:
    """Format the envvars of a `click.Option` or `click.Argument`."""
    yield '.. envvar:: {}'.format(param.envvar)
    yield '   :noindex:'
    yield ''
    if isinstance(param, click.Argument):
        param_ref = param.human_readable_name
    else:
        # if a user has defined an opt with multiple "aliases", always use the
        # first. For example, if '--foo' or '-f' are possible, use '--foo'.
        param_ref = param.opts[0]

    yield _indent('Provide a default for :option:`{}`'.format(param_ref))


@_process_lines("sphinx-click-process-envars")
def _format_envvars(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format all envvars for a `click.Command`."""

    auto_envvar_prefix = ctx.auto_envvar_prefix
    if auto_envvar_prefix is not None:
        params = []
        for param in ctx.command.params:
            if not param.envvar:
                param.envvar = f"{auto_envvar_prefix}_{param.name.upper()}"
            params.append(param)
    else:
        params = [x for x in ctx.command.params if x.envvar]

    for param in params:
        yield '.. _{command_name}-{param_name}-{envvar}:'.format(
            command_name=ctx.command_path.replace(' ', '-'),
            param_name=param.name,
            envvar=param.envvar,
        )
        yield ''
        for line in _format_envvar(param):
            yield line
        yield ''


def _format_subcommand(command: click.Command) -> ty.Generator[str, None, None]:
    """Format a sub-command of a `click.Command` or `click.Group`."""
    yield '.. object:: {}'.format(command.name)

    short_help = command.get_short_help_str()

    if short_help:
        yield ''
        for line in statemachine.string2lines(
            short_help, tab_width=4, convert_whitespace=True
        ):
            yield _indent(line)


@_process_lines("sphinx-click-process-epilog")
def _format_epilog(ctx: click.Context) -> ty.Generator[str, None, None]:
    """Format the epilog for a given `click.Command`.

    We parse this as reStructuredText, allowing users to embed rich
    information in their help messages if they so choose.
    """
    if ctx.command.epilog:
        yield from _format_help(ctx.command.epilog)


def _get_lazyload_commands(ctx: click.Context) -> ty.Dict[str, click.Command]:
    commands = {}
    for command in ctx.command.list_commands(ctx):
        commands[command] = ctx.command.get_command(ctx, command)

    return commands


def _filter_commands(
    ctx: click.Context,
    commands: ty.Optional[ty.List[str]] = None,
) -> ty.List[click.Command]:
    """Return list of used commands."""
    lookup = getattr(ctx.command, 'commands', {})
    if not lookup and isinstance(ctx.command, click.MultiCommand):
        lookup = _get_lazyload_commands(ctx)

    if commands is None:
        return sorted(lookup.values(), key=lambda item: item.name)

    return [lookup[command] for command in commands if command in lookup]


def _format_command(
    ctx: click.Context,
    nested: NestedT,
    commands: ty.Optional[ty.List[str]] = None,
) -> ty.Generator[str, None, None]:
    """Format the output of `click.Command`."""
    if ctx.command.hidden:
        return None

    # description

    for line in _format_description(ctx):
        yield line

    yield '.. program:: {}'.format(ctx.command_path)

    # usage

    for line in _format_usage(ctx):
        yield line

    # options

    lines = list(_format_options(ctx))
    if lines:
        # we use rubric to provide some separation without exploding the table
        # of contents
        yield '.. rubric:: Options'
        yield ''

    for line in lines:
        yield line

    # arguments

    lines = list(_format_arguments(ctx))
    if lines:
        yield '.. rubric:: Arguments'
        yield ''

    for line in lines:
        yield line

    # environment variables

    lines = list(_format_envvars(ctx))
    if lines:
        yield '.. rubric:: Environment variables'
        yield ''

    for line in lines:
        yield line

    # description

    for line in _format_epilog(ctx):
        yield line

    # if we're nesting commands, we need to do this slightly differently
    if nested in (NESTED_FULL, NESTED_NONE):
        return

    command_objs = _filter_commands(ctx, commands)

    if command_objs:
        yield '.. rubric:: Commands'
        yield ''

    for command_obj in command_objs:
        # Don't show hidden subcommands
        if command_obj.hidden:
            continue

        for line in _format_subcommand(command_obj):
            yield line
        yield ''


def nested(argument: ty.Optional[str]) -> NestedT:
    values = (NESTED_FULL, NESTED_SHORT, NESTED_NONE, None)

    if argument not in values:
        raise ValueError(
            "%s is not a valid value for ':nested:'; allowed values: %s"
            % directives.format_values(values)
        )

    return ty.cast(NestedT, argument)


class ClickDirective(rst.Directive):
    has_content = False
    required_arguments = 1
    option_spec = {
        'prog': directives.unchanged_required,
        'nested': nested,
        'commands': directives.unchanged,
        'show-nested': directives.flag,
    }

    def _load_module(self, module_path: str) -> ty.Union[click.Command, click.Group]:
        """Load the module."""

        try:
            module_name, attr_name = module_path.split(':', 1)
        except ValueError:  # noqa
            raise self.error(
                '"{}" is not of format "module:parser"'.format(module_path)
            )

        try:
            with mock(self.env.config.sphinx_click_mock_imports):
                mod = __import__(module_name, globals(), locals(), [attr_name])
        except (Exception, SystemExit) as exc:  # noqa
            err_msg = 'Failed to import "{}" from "{}". '.format(attr_name, module_name)
            if isinstance(exc, SystemExit):
                err_msg += 'The module appeared to call sys.exit()'
            else:
                err_msg += 'The following exception was raised:\n{}'.format(
                    traceback.format_exc()
                )

            raise self.error(err_msg)

        if not hasattr(mod, attr_name):
            raise self.error(
                'Module "{}" has no attribute "{}"'.format(module_name, attr_name)
            )

        parser = getattr(mod, attr_name)

        if not isinstance(parser, (click.Command, click.Group)):
            raise self.error(
                '"{}" of type "{}" is not click.Command or click.Group.'
                '"click.BaseCommand"'.format(type(parser), module_path)
            )
        return parser

    def _generate_nodes(
        self,
        name: str,
        command: click.Command,
        parent: ty.Optional[click.Context],
        nested: NestedT,
        commands: ty.Optional[ty.List[str]] = None,
        semantic_group: bool = False,
    ) -> ty.List[nodes.section]:
        """Generate the relevant Sphinx nodes.

        Format a `click.Group` or `click.Command`.

        :param name: Name of command, as used on the command line
        :param command: Instance of `click.Group` or `click.Command`
        :param parent: Instance of `click.Context`, or None
        :param nested: The granularity of subcommand details.
        :param commands: Display only listed commands or skip the section if
            empty
        :param semantic_group: Display command as title and description for
            `click.CommandCollection`.
        :returns: A list of nested docutil nodes
        """
        ctx = click.Context(command, info_name=name, parent=parent)

        if command.hidden:
            return []

        # Title

        section = nodes.section(
            '',
            nodes.title(text=name),
            ids=[nodes.make_id(ctx.command_path)],
            names=[nodes.fully_normalize_name(ctx.command_path)],
        )

        # Summary
        source_name = ctx.command_path
        result = statemachine.StringList()

        ctx.meta["sphinx-click-env"] = self.env
        if semantic_group:
            lines = _format_description(ctx)
        else:
            lines = _format_command(ctx, nested, commands)

        for line in lines:
            LOG.debug(line)
            result.append(line, source_name)

        sphinx_nodes.nested_parse_with_titles(self.state, result, section)

        # Subcommands

        if nested == NESTED_FULL:
            if isinstance(command, click.CommandCollection):
                for source in command.sources:
                    section.extend(
                        self._generate_nodes(
                            source.name,
                            source,
                            parent=ctx,
                            nested=nested,
                            semantic_group=True,
                        )
                    )
            else:
                commands = _filter_commands(ctx, commands)
                for command in commands:
                    parent = ctx if not semantic_group else ctx.parent
                    section.extend(
                        self._generate_nodes(
                            command.name, command, parent=parent, nested=nested
                        )
                    )

        return [section]

    def run(self) -> ty.Sequence[nodes.section]:
        self.env = self.state.document.settings.env

        command = self._load_module(self.arguments[0])

        if 'prog' not in self.options:
            raise self.error(':prog: must be specified')

        prog_name = self.options['prog']
        show_nested = 'show-nested' in self.options
        nested = self.options.get('nested')

        if show_nested:
            if nested:
                raise self.error(
                    "':nested:' and ':show-nested:' are mutually exclusive"
                )
            else:
                warnings.warn(
                    "':show-nested:' is deprecated; use ':nested: full'",
                    DeprecationWarning,
                )
                nested = NESTED_FULL if show_nested else NESTED_SHORT

        commands = None
        if self.options.get('commands'):
            commands = [
                command.strip() for command in self.options['commands'].split(',')
            ]

        return self._generate_nodes(prog_name, command, None, nested, commands)


def setup(app: application.Sphinx) -> ty.Dict[str, ty.Any]:
    # Need autodoc to support mocking modules
    app.setup_extension('sphinx.ext.autodoc')
    app.add_directive('click', ClickDirective)

    app.add_event("sphinx-click-process-description")
    app.add_event("sphinx-click-process-usage")
    app.add_event("sphinx-click-process-options")
    app.add_event("sphinx-click-process-arguments")
    app.add_event("sphinx-click-process-envvars")
    app.add_event("sphinx-click-process-epilog")
    app.add_config_value(
        'sphinx_click_mock_imports', lambda config: config.autodoc_mock_imports, 'env'
    )

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
