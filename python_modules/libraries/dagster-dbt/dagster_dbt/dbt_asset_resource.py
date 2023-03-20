from typing import Any, Iterator, Mapping, Optional, Union, cast

import dbt.version
from dagster import AssetObservation, ConfigurableResource, Output
from packaging import version

from dagster_dbt.asset_decorators import DbtExecutionContext
from dagster_dbt.cli.utils import execute_cli, execute_cli_stream
from dagster_dbt.utils import result_to_events, structured_json_line_to_events


class DbtAssetResource(ConfigurableResource):
    project_dir: str
    profiles_dir: Optional[str]
    default_flags: Mapping[str, Any] = {}
    executable: str = "dbt"
    json_log_format: bool = True
    warn_error: bool = False
    ignore_handled_error: bool = True
    debug: bool = False
    target_path: str = "target"

    @property
    def can_stream_events(self) -> bool:
        # versions prior to 1.4.0 do not support streaming events
        return self.json_log_format and version.parse(dbt.version.__version__) >= version.parse(
            "1.4.0"
        )

    def _get_flags(
        self, context: DbtExecutionContext, kwargs: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        return {
            "project-dir": self.project_dir,
            "profiles-dir": self.profiles_dir,
            **self.default_flags,
            **context.get_dbt_selection_kwargs(),
            **kwargs,
        }

    def cli(
        self, context: DbtExecutionContext, command: str, **kwargs
    ) -> Iterator[Union[Output, AssetObservation]]:
        flags = self._get_flags(context, kwargs)

        if self.can_stream_events:
            for event in execute_cli_stream(
                executable=self.executable,
                command=command,
                flags_dict=flags,
                log=context.log,
                warn_error=self.warn_error,
                ignore_handled_error=self.ignore_handled_error,
                json_log_format=self.json_log_format,
            ):
                if event.parsed_json_line is not None:
                    yield from structured_json_line_to_events(
                        event.parsed_json_line,
                        context=context,
                        node_info_to_asset_key=context.asset_key_fn,
                        runtime_metadata_fn=None,
                        manifest_json=context.manifest_dict,
                    )
        else:
            dbt_output = execute_cli(
                executable=self.executable,
                command=command,
                flags_dict=flags,
                log=context.log,
                warn_error=self.warn_error,
                ignore_handled_error=self.ignore_handled_error,
                json_log_format=self.json_log_format,
                target_path=self.target_path,
            )
            for event in result_to_events(
                dbt_output.result["results"],
                node_info_to_asset_key=context.asset_key_fn,
                generate_asset_outputs=True,
            ):
                yield cast(Union[Output, AssetObservation], event)

    def run(
        self, context: DbtExecutionContext, **kwargs
    ) -> Iterator[Union[Output, AssetObservation]]:
        yield from self.cli(context, "run", **kwargs)

    def build(
        self, context: DbtExecutionContext, **kwargs
    ) -> Iterator[Union[Output, AssetObservation]]:
        yield from self.cli(context, "build", **kwargs)
