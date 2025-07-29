import sys
import textwrap
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import DgRawCliConfig, normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_editable_dagster_options, dg_global_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.cli.plus.constants import DgPlusAgentPlatform
from dagster_dg_cli.utils.plus.build import (
    create_deploy_dockerfile,
    get_agent_type_and_platform_from_graphql,
    get_dockerfile_path,
)
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient


def _get_scaffolded_container_context_yaml(agent_platform: DgPlusAgentPlatform) -> Optional[str]:
    if agent_platform == DgPlusAgentPlatform.K8S:
        return textwrap.dedent(
            """
            ### Uncomment to add configuration for k8s resources.
            # k8s:
            #   server_k8s_config: # Raw kubernetes config for code servers launched by the agent
            #     pod_spec_config: # Config for the code server pod spec
            #       node_selector:
            #         disktype: standard
            #     pod_template_spec_metadata: # Metadata for the code server pod
            #       annotations:
            #         mykey: myvalue
            #     container_config: # Config for the main dagster container in the code server pod
            #       resources:
            #         limits:
            #           cpu: 100m
            #           memory: 128Mi
            #   run_k8s_config: # Raw kubernetes config for runs launched by the agent
            #     pod_spec_config: # Config for the run's PodSpec
            #       node_selector:
            #         disktype: ssd
            #     container_config: # Config for the main dagster container in the run pod
            #       resources:
            #         limits:
            #           cpu: 500m
            #           memory: 1024Mi
            #     pod_template_spec_metadata: # Metadata for the run pod
            #       annotations:
            #         mykey: myvalue
            #     job_spec_config: # Config for the Kubernetes job for the run
            #       ttl_seconds_after_finished: 7200
            """
        )
    elif agent_platform == DgPlusAgentPlatform.ECS:
        return textwrap.dedent(
            """
            ### Uncomment to add configuration for ECS resources.
            # ecs:
            #   env_vars:
            #     - DATABASE_NAME=staging
            #     - DATABASE_PASSWORD
            #   secrets:
            #     - name: 'MY_API_TOKEN'
            #       valueFrom: 'arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:token::'
            #     - name: 'MY_PASSWORD'
            #       valueFrom: 'arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:password::'
            #   server_resources: # Resources for code servers launched by the agent for this location
            #     cpu: "256"
            #     memory: "512"
            #   run_resources: # Resources for runs launched by the agent for this location
            #     cpu: "4096"
            #     memory: "16384"
            #   execution_role_arn: arn:aws:iam::123456789012:role/MyECSExecutionRole
            #   task_role_arn: arn:aws:iam::123456789012:role/MyECSTaskRole
            #   mount_points:
            #     - sourceVolume: myEfsVolume
            #       containerPath: '/mount/efs'
            #       readOnly: True
            #   volumes:
            #     - name: myEfsVolume
            #       efsVolumeConfiguration:
            #         fileSystemId: fs-1234
            #         rootDirectory: /path/to/my/data
            #   server_sidecar_containers:
            #     - name: DatadogAgent
            #       image: public.ecr.aws/datadog/agent:latest
            #       environment:
            #         - name: ECS_FARGATE
            #           value: true
            #   run_sidecar_containers:
            #     - name: DatadogAgent
            #       image: public.ecr.aws/datadog/agent:latest
            #       environment:
            #         - name: ECS_FARGATE
            #           value: true
            """
        )
    elif agent_platform == DgPlusAgentPlatform.DOCKER:
        return textwrap.dedent(
            """
            ### Uncomment to add configuration for Docker resources.
            # docker:
            #   env_vars:
            #     - DATABASE_NAME=staging
            #     - DATABASE_PASSWORD
            """
        )
    else:
        return None


def _get_project_contexts(dg_context: DgContext, cli_config: DgRawCliConfig) -> list[DgContext]:
    if dg_context.is_in_workspace:
        return [
            dg_context.for_project_environment(project.path, cli_config)
            for project in dg_context.project_specs
        ]
    else:
        return [dg_context]


@click.command(name="build-artifacts", cls=DgClickCommand)
@click.option(
    "--python-version",
    "python_version",
    type=click.Choice(["3.9", "3.10", "3.11", "3.12", "3.13"]),
    help=(
        "Python version used to deploy the project. If not set, defaults to the calling process's Python minor version."
    ),
)
@click.option(
    "-y",
    "--yes",
    "skip_confirmation_prompt",
    is_flag=True,
    help="Skip confirmation prompts.",
)
@dg_editable_dagster_options
@dg_global_options
@cli_telemetry_wrapper
def scaffold_build_artifacts_command(
    python_version: Optional[str],
    use_editable_dagster: Optional[str],
    skip_confirmation_prompt: bool,
    **global_options: object,
) -> None:
    """Scaffolds a Dockerfile to build the given Dagster project or workspace."""
    import yaml

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)

    plus_config = DagsterPlusCliConfig.get() if DagsterPlusCliConfig.exists() else None

    if plus_config:
        gql_client = DagsterPlusGraphQLClient.from_config(plus_config)
        _, agent_platform = get_agent_type_and_platform_from_graphql(gql_client)
    else:
        agent_platform = DgPlusAgentPlatform.UNKNOWN

    scaffolded_container_context_yaml = _get_scaffolded_container_context_yaml(agent_platform)

    if not dg_context.is_project:
        click.echo("Scaffolding build artifacts for workspace...")

        create = True
        if dg_context.build_config_path.exists():
            create = skip_confirmation_prompt or click.confirm(
                f"Build config already exists at {dg_context.build_config_path}. Overwrite it?",
            )
        if create:
            dg_context.build_config_path.write_text(yaml.dump({"registry": "..."}))
            click.echo(f"Workspace build config created at {dg_context.build_config_path}.")

        if scaffolded_container_context_yaml:
            create = True
            if dg_context.container_context_config_path.exists():
                create = skip_confirmation_prompt or click.confirm(
                    f"Container config already exists at {dg_context.container_context_config_path}. Overwrite it?",
                )
            if create:
                dg_context.container_context_config_path.write_text(
                    scaffolded_container_context_yaml
                )
                click.echo(
                    f"Workspace container config created at {dg_context.container_context_config_path}."
                )

    project_contexts = _get_project_contexts(dg_context, cli_config)
    for project_context in project_contexts:
        click.echo(f"Scaffolding build artifacts for {project_context.code_location_name}...")

        create = True
        if project_context.build_config_path.exists():
            create = skip_confirmation_prompt or click.confirm(
                f"Build config already exists at {project_context.build_config_path}. Overwrite it?",
            )
        if create:
            project_context.build_config_path.write_text(
                textwrap.dedent(
                    """
                    directory: .
                    # Registry is specified in the build.yaml file at the root of the workspace,
                    # but can be overridden here.
                    # registry: '...'
                    """
                )
                if dg_context.is_in_workspace
                else textwrap.dedent(
                    """
                    directory: .
                    registry: '...'
                    """
                )
            )
            click.echo(f"Project build config created at {project_context.build_config_path}.")

        if scaffolded_container_context_yaml:
            if project_context.container_context_config_path.exists():
                create = skip_confirmation_prompt or click.confirm(
                    f"Container config already exists at {project_context.container_context_config_path}. Overwrite it?",
                )
            if create:
                project_context.container_context_config_path.write_text(
                    scaffolded_container_context_yaml
                )
                click.echo(
                    f"Project container config created at {project_context.container_context_config_path}."
                )

        dockerfile_path = get_dockerfile_path(project_context, workspace_context=dg_context)
        create = True
        if dockerfile_path.exists():
            create = skip_confirmation_prompt or click.confirm(
                f"A Dockerfile already exists at {dockerfile_path}. Overwrite it?",
            )
        if create:
            create_deploy_dockerfile(
                dockerfile_path,
                python_version or f"3.{sys.version_info.minor}",
                bool(use_editable_dagster),
            )
            click.echo(f"Dockerfile created at {dockerfile_path}.")
