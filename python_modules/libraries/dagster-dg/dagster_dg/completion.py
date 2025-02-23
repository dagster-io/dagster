import click
import click.shell_completion
import shellingham
import typer._completion_shared

from dagster_dg.utils import exit_with_error


def install_completion(context: click.Context):
    # Click on its own does not support automatic installation of completion scripts, but `typer`
    # does. However, we don't use `typer` for our app, and the typer completion script is not the
    # same as the click completion script (nor is it compatible with a pure-click app). But the
    # typer automatic installation routine works for any completion script.
    #
    # Therefore, we:
    #
    # 1. Generate the click completion script and store it in a string.
    # 2. Overwrite the typer completion script, stored in an internal dictionary, with the
    #    click-generated one.
    # 3. Call the typer installation routine, which will then install the click-generated script.
    #
    # This is obviously hacky and non-ideal, but it works and is probably superior to maintaining
    # our own completion installation logic across shells.

    shell, _ = shellingham.detect_shell()
    comp_class = click.shell_completion.get_completion_class(shell)
    if comp_class is None:
        exit_with_error(f"Shell `{shell}` is not supported.")
    else:
        comp_inst = comp_class(
            cli=context.command, ctx_args={}, prog_name="dg", complete_var="_DG_COMPLETE"
        )
        source = comp_inst.source()

        # Overwrite typer's stored completion script with the click-generated one.
        typer._completion_shared._completion_scripts[shell] = source  # noqa: SLF001

        # Invoke typer's completion installation routine. It will install the click-generated
        # script because we've injected it in the right place.
        shell, path = typer._completion_shared.install(shell=shell, prog_name="dg")  # noqa: SLF001

        # Notify the user.
        click.secho(f"{shell} completion installed in {path}", fg="green")
        click.echo("Completion will take effect once you restart the terminal")
        context.exit(0)
