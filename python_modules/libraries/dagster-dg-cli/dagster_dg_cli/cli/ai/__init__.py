import click
from dagster_dg_core.utils import DgClickGroup


class AiGroup(DgClickGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._commands_defined = False

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        self._define_commands()
        return super().get_command(ctx, cmd_name)

    def list_commands(self, ctx: click.Context) -> list[str]:
        self._define_commands()
        return super().list_commands(ctx)

    def _define_commands(self) -> None:
        if self._commands_defined:
            return

        # Lazy import keeps the top-level dg CLI import lightweight until AI commands are requested.
        from dagster_dg_cli.cli.ai.dispatch import dispatch_command

        self.add_command(dispatch_command)
        self._commands_defined = True


@click.group(name="ai", cls=AiGroup)
def ai_group() -> None:
    """AI-powered CLI commands."""
