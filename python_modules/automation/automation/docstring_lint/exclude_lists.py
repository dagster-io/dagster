"""Hardcoded exclude lists for public API validation.

This file contains all the symbols that are known to have @public API inconsistencies.
These lists allow incremental fixing while preventing new issues from being introduced.
"""

# Symbols marked @public but not yet documented in RST files
EXCLUDE_MISSING_RST = {
    # Components system - new functionality being developed
    "dagster.components.definitions.definitions",
    "dagster.components.core.load_defs.build_defs_for_component",
    "dagster.components.core.load_defs.load_from_defs_folder",
    "dagster.components.core.defs_module.DefsFolderComponent",
    "dagster.components.core.context.ComponentDeclLoadContext",
    "dagster.components.core.context.ComponentLoadContext",
    "dagster.components.component.component_loader.component",
    "dagster.components.component.component_loader.component_instance",
    "dagster.components.component.component.ComponentTypeSpec",
    "dagster.components.component.component.Component",
    "dagster.components.resolved.model.Model",
    "dagster.components.resolved.model.Resolver",
    "dagster.components.resolved.context.ResolutionContext",
    "dagster.components.resolved.base.Resolvable",
    "dagster.components.scaffold.scaffold.scaffold_with",
    "dagster.components.scaffold.scaffold.ScaffoldRequest",
    "dagster.components.scaffold.scaffold.Scaffolder",
    "dagster.components.lib.sql_component.sql_component.SqlComponent",
    "dagster.components.core.tree.ComponentTree",
    "dagster._core.errors.user_code_error_boundary",
    # Core internal functionality
    "dagster._core.definitions.definitions_class.create_repository_using_definitions_args",
    # Core storage and compute management - internal functionality
    "dagster._core.storage.compute_log_manager.ForkedPdb",
    "dagster._core.definitions.output.DynamicOutputDefinition",
    "dagster._core.storage.file_manager.FileManager",
    "dagster._core.instance.ref.InstanceRef",
    "dagster._core.storage.event_log.base.AssetRecord",
    "dagster._core.storage.event_log.base.EventLogStorage",
    "dagster._core.storage.schedules.base.ScheduleStorage",
    "dagster._core.storage.runs.base.RunStorage",
    "dagster._core.storage.event_log.sqlite.consolidated_sqlite_event_log.ConsolidatedSqliteEventLogStorage",
    # Component exports at top level
    "dagster.build_defs_for_component",
    "dagster.ComponentTypeSpec",
    "dagster.scaffold_with",
    "dagster.ScaffoldRequest",
    "dagster.Scaffolder",
    "dagster.SqlComponent",
    "dagster_sling.SlingMode",
    # Additional core internal functionality - internal module paths
    "dagster._utils.forked_pdb.ForkedPdb",
    "dagster._serdes.config_class.ConfigurableClassData",
    "dagster._serdes.config_class.ConfigurableClass",
    "dagster._core.launcher.base.RunLauncher",
    "dagster._core.scheduler.scheduler.Scheduler",
    "dagster._core.storage.compute_log_manager.ComputeLogManager",
    "dagster._core.storage.base_storage.DagsterStorage",
    "dagster._core.storage.noop_compute_log_manager.NoOpComputeLogManager",
    "dagster._core.storage.root.LocalArtifactStorage",
    "dagster._core.storage.local_compute_log_manager.LocalComputeLogManager",
    # Storage classes with @public decorators but missing RST documentation
    "dagster._core.storage.event_log.sql_event_log.SqlEventLogStorage",
    "dagster._core.storage.schedules.sql_schedule_storage.SqlScheduleStorage",
    "dagster._core.storage.runs.sql_run_storage.SqlRunStorage",
    "dagster._core.storage.event_log.sqlite.sqlite_event_log.SqliteEventLogStorage",
    "dagster._core.storage.schedules.sqlite.sqlite_schedule_storage.SqliteScheduleStorage",
    "dagster._core.storage.runs.sqlite.sqlite_run_storage.SqliteRunStorage",
    # Library pipes clients
    "dagster_aws.pipes.clients.emr_containers.PipesEMRContainersClient",
    "dagster_aws.pipes.clients.emr.PipesEMRClient",
    "dagster_aws.pipes.clients.emr_serverless.PipesEMRServerlessClient",
    "dagster_gcp.pipes.clients.dataproc_job.PipesDataprocJobClient",
    # Library resources
    "dagster_openai.resources.with_usage_metadata",
    "dagster_openai.resources.OpenAIResource",
    "dagster_sling.SlingMode",
    "dagster_sling.resources.SlingConnectionResource",
    # New public APIs missing RST documentation
    "dagster.build_defs_for_component",
    "dagster.ComponentTypeSpec",
    "dagster.scaffold_with",
    "dagster.ScaffoldRequest",
    "dagster.Scaffolder",
    "dagster.SqlComponent",
    # Library components
    "dagster_snowflake.components.sql_component.component.SnowflakeConnectionComponentBase",
    # GitHub resources and clients - new functionality being added
    "dagster_github.resources.GithubClient",
    "dagster_prometheus.resources.PrometheusClient",
    # Azure cloud storage and compute resources
    "dagster_azure.blob.compute_log_manager.AzureBlobComputeLogManager",
    "dagster_azure.adls2.file_manager.ADLS2FileHandle",
    # DBT integration components
    "dagster_dbt.core.dbt_event_iterator.DbtEventIterator",
    # Airlift migration tools - active development
    "dagster_airlift.mwaa.auth.MwaaSessionAuthBackend",
    "dagster_airlift.in_airflow.proxying_fn.proxying_to_dagster",
    "dagster_airlift.in_airflow.dag_proxy_operator.BaseProxyDAGToDagsterOperator",
    "dagster_airlift.in_airflow.dag_proxy_operator.DefaultProxyDAGToDagsterOperator",
    "dagster_airlift.in_airflow.base_asset_operator.BaseDagsterAssetsOperator",
    "dagster_airlift.in_airflow.proxied_state.TaskProxiedState",
    "dagster_airlift.in_airflow.proxied_state.DagProxiedState",
    "dagster_airlift.in_airflow.proxied_state.AirflowProxiedState",
    "dagster_airlift.in_airflow.proxied_state.load_proxied_state_from_yaml",
    "dagster_airlift.in_airflow.task_proxy_operator.BaseProxyTaskToDagsterOperator",
    "dagster_airlift.in_airflow.task_proxy_operator.DefaultProxyTaskToDagsterOperator",
    "dagster_airlift.core.top_level_dag_def_api.assets_with_task_mappings",
    "dagster_airlift.core.top_level_dag_def_api.assets_with_dag_mappings",
    "dagster_airlift.core.load_defs.build_defs_from_airflow_instance",
    "dagster_airlift.core.basic_auth.AirflowBasicAuthBackend",
    "dagster_airlift.core.airflow_instance.AirflowAuthBackend",
    "dagster_airlift.core.airflow_instance.AirflowInstance",
    "dagster_airlift.core.airflow_defs_data.AirflowDefinitionsData",
    "dagster_airlift.core.multiple_tasks.TaskHandleDict",
    "dagster_airlift.core.serialization.serialized_data.DagInfo",
    "dagster_airlift.core.components.airflow_instance.component.AirflowInstanceComponent",
    "dagster_airlift.core.components.task_asset_spec.component.TaskAssetSpecComponent",
    "dagster_airlift.core.components.dag_asset_spec.component.DagAssetSpecComponent",
    "dagster_embedded_elt.sling.resources.SlingMode",
    "dagster_embedded_elt.sling.resources.SlingConnectionResource",
    "dagster_embedded_elt.sling.asset_decorator.sling_assets",
    "dagster_embedded_elt.dlt.resources.DltResource",
    "dagster_embedded_elt.dlt.asset_decorator.dlt_assets",
    "dagster_snowflake.snowflake_pandas_type_handler.SnowflakePandasTypeHandler",
    "dagster_snowflake.snowflake_pandas_type_handler.DagsterSnowflakeError",
    "dagster_snowflake.resources.SnowflakeResource",
    "dagster_snowflake.resources.SnowflakeConnection",
    "dagster_snowflake.pipes.clients.SnowflakePipesClient",
    "dagster_k8s.models.k8s_model.K8sModel",
    "dagster_k8s.job.construct_dagster_k8s_job",
    "dagster_k8s.launcher.user_defined_k8s_config.UserDefinedDagsterK8sConfig",
    "dagster_aws.s3.compute_log_manager.S3ComputeLogManager",
    "dagster_aws.s3.file_manager.S3FileHandle",
    "dagster_aws.emr.emr_step_main.emr_step_main",
    "dagster_aws.emr.types.EmrError",
    "dagster_aws.ssm.ssm_client_resource.ParameterStoreTag",
    "dagster_gcp.gcs.compute_log_manager.GCSComputeLogManager",
    "dagster_duckdb_pyspark.type_handler.DuckDBPySparkTypeHandler",
    "dagster_graphql.client.dagster_graphql_client.DagsterGraphQLClient",
    "dagster_graphql.client.util.InvalidOutputErrorInfo",
    "dagster_graphql.client.util.ReloadRepositoryLocationInfo",
    "dagster_graphql.client.util.ReloadRepositoryLocationStatus",
    # Additional GCP pipe components
    "dagster_gcp.pipes.message_readers.PipesGCSMessageReader",
    "dagster_gcp.pipes.context_injectors.PipesGCSContextInjector",
    # DuckDB type handlers
    "dagster_duckdb_pandas.duckdb_pandas_type_handler.DuckDBPandasTypeHandler",
    "dagster_duckdb_pyspark.duckdb_pyspark_type_handler.DuckDBPySparkTypeHandler",
    "dagster_duckdb_polars.duckdb_polars_type_handler.DuckDBPolarsTypeHandler",
    # AWS components with correct module paths
    "dagster_aws.ssm.resources.ParameterStoreTag",
    "dagster_aws.emr.emr.EmrError",
    "dagster_aws.pipes.message_readers.PipesS3MessageReader",
    "dagster_aws.pipes.message_readers.PipesCloudWatchMessageReader",
    "dagster_aws.pipes.context_injectors.PipesS3ContextInjector",
    "dagster_aws.pipes.context_injectors.PipesLambdaEventContextInjector",
    "dagster_aws.pipes.clients.lambda_.PipesLambdaClient",
    "dagster_aws.pipes.clients.glue.PipesGlueClient",
    "dagster_aws.pipes.clients.ecs.PipesECSClient",
    # Tableau integration components
    "dagster_tableau.assets.build_tableau_materializable_assets_definition",
    "dagster_tableau.resources.load_tableau_asset_specs",
    "dagster_tableau.resources.TableauCloudWorkspace",
    "dagster_tableau.resources.TableauServerWorkspace",
    "dagster_tableau.asset_decorator.tableau_assets",
    "dagster_tableau.translator.DagsterTableauTranslator",
    "dagster_tableau.asset_utils.parse_tableau_external_and_materializable_asset_specs",
    # Weights & Biases integration
    "dagster_wandb.types.SerializationModule",
    "dagster_wandb.launch.ops.run_launch_agent",
    "dagster_wandb.launch.ops.run_launch_job",
}

# Symbols marked @public but not exported at top-level
EXCLUDE_MISSING_EXPORT = {
    # These are internal symbols that should either be exported or have @public removed
    "dagster._core.definitions.definitions_class.create_repository_using_definitions_args",
    "dagster.components.core.load_defs.build_defs_for_component",
    "dagster.components.core.load_defs.load_from_defs_folder",
    "dagster.components.core.defs_module.DefsFolderComponent",
    "dagster.components.core.context.ComponentDeclLoadContext",
    "dagster.components.core.context.ComponentLoadContext",
    "dagster.components.component.component_loader.component",
    "dagster.components.component.component_loader.component_instance",
    "dagster.components.component.component.ComponentTypeSpec",
    "dagster.components.component.component.Component",
    "dagster.components.resolved.model.Model",
    "dagster.components.resolved.model.Resolver",
    "dagster.components.resolved.context.ResolutionContext",
    "dagster.components.resolved.base.Resolvable",
    "dagster.components.scaffold.scaffold.scaffold_with",
    "dagster.components.scaffold.scaffold.ScaffoldRequest",
    "dagster.components.scaffold.scaffold.Scaffolder",
    "dagster._core.errors.user_code_error_boundary",
    # Library resources that have @public but are not top-level exported
    "dagster_github.resources.GithubClient",
    "dagster_prometheus.resources.PrometheusClient",
    "dagster_azure.blob.compute_log_manager.AzureBlobComputeLogManager",
    "dagster_azure.adls2.file_manager.ADLS2FileHandle",
    "dagster_dbt.core.dbt_event_iterator.DbtEventIterator",
    "dagster_airlift.mwaa.auth.MwaaSessionAuthBackend",
    "dagster_airlift.in_airflow.proxying_fn.proxying_to_dagster",
    "dagster_airlift.in_airflow.dag_proxy_operator.BaseProxyDAGToDagsterOperator",
    "dagster_airlift.in_airflow.dag_proxy_operator.DefaultProxyDAGToDagsterOperator",
    "dagster_airlift.in_airflow.base_asset_operator.BaseDagsterAssetsOperator",
    "dagster_airlift.in_airflow.proxied_state.TaskProxiedState",
    "dagster_airlift.in_airflow.proxied_state.DagProxiedState",
    "dagster_airlift.in_airflow.proxied_state.AirflowProxiedState",
    "dagster_airlift.in_airflow.proxied_state.load_proxied_state_from_yaml",
    "dagster_airlift.in_airflow.task_proxy_operator.BaseProxyTaskToDagsterOperator",
    "dagster_airlift.in_airflow.task_proxy_operator.DefaultProxyTaskToDagsterOperator",
    "dagster_airlift.core.top_level_dag_def_api.assets_with_task_mappings",
    "dagster_airlift.core.top_level_dag_def_api.assets_with_dag_mappings",
    "dagster_airlift.core.load_defs.build_defs_from_airflow_instance",
    "dagster_airlift.core.basic_auth.AirflowBasicAuthBackend",
    "dagster_airlift.core.airflow_instance.AirflowAuthBackend",
    "dagster_airlift.core.airflow_instance.AirflowInstance",
    "dagster_airlift.core.airflow_defs_data.AirflowDefinitionsData",
    "dagster_airlift.core.multiple_tasks.TaskHandleDict",
    "dagster_airlift.core.serialization.serialized_data.DagInfo",
    "dagster_airlift.core.components.airflow_instance.component.AirflowInstanceComponent",
    "dagster_airlift.core.components.task_asset_spec.component.TaskAssetSpecComponent",
    "dagster_airlift.core.components.dag_asset_spec.component.DagAssetSpecComponent",
    "dagster_embedded_elt.sling.resources.SlingMode",
    "dagster_embedded_elt.sling.resources.SlingConnectionResource",
    "dagster_embedded_elt.sling.asset_decorator.sling_assets",
    "dagster_embedded_elt.dlt.resources.DltResource",
    "dagster_embedded_elt.dlt.asset_decorator.dlt_assets",
    "dagster_snowflake.snowflake_pandas_type_handler.SnowflakePandasTypeHandler",
    "dagster_snowflake.snowflake_pandas_type_handler.DagsterSnowflakeError",
    "dagster_snowflake.resources.SnowflakeResource",
    "dagster_snowflake.resources.SnowflakeConnection",
    "dagster_snowflake.pipes.clients.SnowflakePipesClient",
    "dagster_k8s.models.k8s_model.K8sModel",
    "dagster_k8s.job.construct_dagster_k8s_job",
    "dagster_k8s.launcher.user_defined_k8s_config.UserDefinedDagsterK8sConfig",
    "dagster_aws.s3.compute_log_manager.S3ComputeLogManager",
    "dagster_aws.s3.file_manager.S3FileHandle",
    "dagster_aws.emr.emr_step_main.emr_step_main",
    "dagster_aws.emr.types.EmrError",
    "dagster_aws.ssm.ssm_client_resource.ParameterStoreTag",
    "dagster_gcp.gcs.compute_log_manager.GCSComputeLogManager",
    "dagster_duckdb_pyspark.type_handler.DuckDBPySparkTypeHandler",
    "dagster_graphql.client.dagster_graphql_client.DagsterGraphQLClient",
    "dagster_graphql.client.util.InvalidOutputErrorInfo",
    "dagster_graphql.client.util.ReloadRepositoryLocationInfo",
    "dagster_graphql.client.util.ReloadRepositoryLocationStatus",
    # Additional GCP pipe components not exported at top level
    "dagster_gcp.pipes.message_readers.PipesGCSMessageReader",
    "dagster_gcp.pipes.context_injectors.PipesGCSContextInjector",
    "dagster_gcp.gcs.sensor.get_gcs_keys",
    # DuckDB type handlers not exported at top level
    "dagster_duckdb_pandas.duckdb_pandas_type_handler.DuckDBPandasTypeHandler",
    "dagster_duckdb_pyspark.duckdb_pyspark_type_handler.DuckDBPySparkTypeHandler",
    "dagster_duckdb_polars.duckdb_polars_type_handler.DuckDBPolarsTypeHandler",
    # Fivetran event iterator
    "dagster_fivetran.fivetran_event_iterator.FivetranEventIterator",
    # AWS components with correct module paths not exported at top level
    "dagster_aws.ssm.resources.ParameterStoreTag",
    "dagster_aws.emr.emr.EmrError",
    "dagster_aws.pipes.message_readers.PipesS3MessageReader",
    "dagster_aws.pipes.message_readers.PipesCloudWatchMessageReader",
    "dagster_aws.pipes.context_injectors.PipesS3ContextInjector",
    "dagster_aws.pipes.context_injectors.PipesLambdaEventContextInjector",
    "dagster_aws.pipes.clients.lambda_.PipesLambdaClient",
    "dagster_aws.pipes.clients.glue.PipesGlueClient",
    "dagster_aws.pipes.clients.ecs.PipesECSClient",
    # Tableau integration components not exported at top level
    "dagster_tableau.assets.build_tableau_materializable_assets_definition",
    "dagster_tableau.resources.load_tableau_asset_specs",
    "dagster_tableau.resources.TableauCloudWorkspace",
    "dagster_tableau.resources.TableauServerWorkspace",
    "dagster_tableau.asset_decorator.tableau_assets",
    "dagster_tableau.translator.DagsterTableauTranslator",
    "dagster_tableau.asset_utils.parse_tableau_external_and_materializable_asset_specs",
    # Weights & Biases integration not exported at top level
    "dagster_wandb.types.SerializationModule",
    "dagster_wandb.launch.ops.run_launch_agent",
    "dagster_wandb.launch.ops.run_launch_job",
}

# List of symbols missing @public decorators
EXCLUDE_MISSING_PUBLIC = {
    "dagster_pipes.encode_env_var",  # Bare module-level symbol - does not support @public decorator
    "dagster_pipes.decode_env_var",  # Bare module-level symbol - does not support @public decorator
    "dagstermill.get_context",  # Legacy dagstermill API that may be deprecated
    "dagstermill.yield_event",  # Legacy dagstermill API that may be deprecated
    "dagstermill.yield_result",  # Legacy dagstermill API that may be deprecated
    "dagster_iceberg.config.IcebergCatalogConfig",  # Configuration class that should be used through higher-level APIs
    "dagster_iceberg.handler.IcebergBaseTypeHandler",  # Base class for internal type handling, not direct user API
    "dagster_iceberg.io_manager.base.IcebergIOManager",  # Base class for internal implementation, not direct user API
    "dagster_airbyte.airbyte_assets",  # Factory function that should be used through higher-level asset APIs
    "dagster_airlift.DagSelectorFn",  # Type alias - does not support @public decorator
    "dagster_airlift.DagsterEventTransformerFn",  # Type alias - does not support @public decorator
    "dagster_fivetran.ConnectorSelectorFn",  # Type alias - does not support @public decorator
    "dagster.PreviewWarning",  # Warning class used internally by framework, not user-facing API
    "dagster.BetaWarning",  # Warning class used internally by framework, not user-facing API
    "dagster.SupersessionWarning",  # Warning class used internally by framework, not user-facing API
    "dagster.file_relative_path",  # Utility function that may be deprecated in favor of pathlib
    "dagster.DefaultRunCoordinator",  # Bare module-level symbol - does not support @public decorator
    # Additional symbols documented in RST but missing @public decorators
    "dagster.configured",  # Core configuration utility function
    "dagster.ForkedPdb",  # Internal debugging utility
    "dagster.FileManager",  # Core storage management interface
    "dagster.InstanceRef",  # Core instance reference type
    "dagster.ConfigurableClass",  # Base class for configurable components
    "dagster.ConfigurableClassData",  # Data structure for configurable class information
    "dagster.LocalArtifactStorage",  # Local artifact storage implementation
    "dagster.DagsterStorage",  # Base storage interface
    "dagster.RunStorage",  # Base run storage interface
    "dagster.SqlRunStorage",  # SQL-based run storage
    "dagster.SqliteRunStorage",  # SQLite run storage implementation
    "dagster.EventLogStorage",  # Base event log storage interface
    "dagster.SqlEventLogStorage",  # SQL-based event log storage
    "dagster.SqliteEventLogStorage",  # SQLite event log storage implementation
    "dagster.ConsolidatedSqliteEventLogStorage",  # Consolidated SQLite event log
    "dagster.AssetRecord",  # Asset record data structure
    "dagster.ComputeLogManager",  # Base compute log manager interface
    "dagster.LocalComputeLogManager",  # Local compute log manager
    "dagster.NoOpComputeLogManager",  # No-op compute log manager
    "dagster.RunLauncher",  # Base run launcher interface
    "dagster.Scheduler",  # Base scheduler interface
    "dagster.ScheduleStorage",  # Base schedule storage interface
    "dagster.SqlScheduleStorage",  # SQL-based schedule storage
    "dagster.SqliteScheduleStorage",  # SQLite schedule storage implementation
    "dagster.user_code_error_boundary",  # Error boundary utility
    # AWS library components
    "dagster_aws.s3.S3ComputeLogManager",  # S3 compute log management
    "dagster_aws.s3.S3FileHandle",  # S3 file handle
    "dagster_aws.emr.emr_step_main",  # EMR step execution
    "dagster_aws.emr.EmrError",  # EMR error handling
    "dagster_aws.ssm.ParameterStoreTag",  # SSM parameter store tagging
    "dagster_aws.pipes.PipesS3ContextInjector",  # S3 context injection for pipes
    "dagster_aws.pipes.PipesLambdaEventContextInjector",  # Lambda event context injection
    "dagster_aws.pipes.PipesS3MessageReader",  # S3 message reading for pipes
    "dagster_aws.pipes.PipesCloudWatchMessageReader",  # CloudWatch message reading
    "dagster_aws.pipes.PipesLambdaClient",  # Lambda pipes client
    "dagster_aws.pipes.PipesGlueClient",  # Glue pipes client
    "dagster_aws.pipes.PipesECSClient",  # ECS pipes client
    "dagster_aws.pipes.PipesEMRClient",  # EMR pipes client
    "dagster_aws.pipes.PipesEMRContainersClient",  # EMR Containers pipes client
    "dagster_aws.pipes.PipesEMRServerlessClient",  # EMR Serverless pipes client
    # GCP library components
    "dagster_gcp.gcs.GCSComputeLogManager",  # GCS compute log management
    "dagster_gcp.pipes.PipesDataprocJobClient",  # Dataproc job pipes client
    "dagster_gcp.pipes.PipesGCSContextInjector",  # GCS context injection
    "dagster_gcp.pipes.PipesGCSMessageReader",  # GCS message reading
    # DBT library components
    "dagster_dbt.core.dbt_cli_invocation.DbtEventIterator",  # DBT event iteration
    # DuckDB PySpark integration
    "dagster_duckdb_pyspark.DuckDBPySparkTypeHandler",  # DuckDB PySpark type handling
    # GraphQL client components
    "dagster_graphql.DagsterGraphQLClient",  # GraphQL client
    "dagster_graphql.InvalidOutputErrorInfo",  # GraphQL error info
    "dagster_graphql.ReloadRepositoryLocationInfo",  # Repository reload info
    "dagster_graphql.ReloadRepositoryLocationStatus",  # Repository reload status
    # DuckDB type handlers documented but missing @public
    "dagster_duckdb_pandas.DuckDBPandasTypeHandler",
    # Pipes context and loaders
    "dagster_pipes.PipesContext",
    "dagster_pipes.PipesContextLoader",
    "dagster_pipes.PipesDefaultContextLoader",
    "dagster_pipes.PipesS3ContextLoader",
    "dagster_pipes.PipesGCSContextLoader",
    "dagster_pipes.PipesDbfsContextLoader",
    "dagster_pipes.PipesAzureBlobStorageContextLoader",
    "dagster_pipes.PipesADLSGen2ContextLoader",
    "dagster_pipes.PipesEnvContextInjector",
    "dagster_pipes.PipesFileContextInjector",
    "dagster_pipes.PipesS3ContextInjector",
    "dagster_pipes.PipesGCSContextInjector",
    "dagster_pipes.PipesDbfsContextInjector",
    "dagster_pipes.PipesAzureBlobStorageContextInjector",
    "dagster_pipes.PipesADLSGen2ContextInjector",
    "dagster_pipes.PipesMessageReader",
    "dagster_pipes.PipesMessageWriter",
    "dagster_pipes.PipesDefaultMessageWriter",
    "dagster_pipes.PipesFileMessageWriter",
    "dagster_pipes.PipesBufferedFilesMessageWriter",
    "dagster_pipes.PipesS3MessageWriter",
    "dagster_pipes.PipesGCSMessageWriter",
    "dagster_pipes.PipesDbfsMessageWriter",
    "dagster_pipes.PipesAzureBlobStorageMessageWriter",
    "dagster_pipes.PipesADLSGen2MessageWriter",
    "dagster_pipes.open_pipes_session",
    # Additional library symbols documented but missing @public
    "dagster_airlift.assets_with_multiple_task_mappings",
    "dagster_aws.emr.EmrJobRunner",
    "dagster_duckdb_polars.DuckDBPolarsTypeHandler",
    "dagster_fivetran.FivetranEventIterator",
    "dagster_fivetran.build_fivetran_assets",
    "dagster_fivetran.load_fivetran_asset_specs",
    "dagster_fivetran.FivetranWorkspace",
    "dagster_fivetran.dagster_fivetran_translator",
    "dagster_github.GithubClient",
    "dagster_looker.LookerResource",
    "dagster_looker.build_looker_pdt_assets_definition",
    "dagster_looker.load_looker_asset_specs",
    "dagster_looker.looker_assets",
    "dagster_looker.DagsterLookerApiTranslator",
    "dagster_looker.build_looker_dashboard_materializable_assets_definition",
    "dagster_looker.RequestStartPdtBuild",
    "dagster_looker.DagsterLookerTranslator",
    "dagster_msteams.msteams_resource",
    "dagster_msteams.make_teams_on_run_failure_sensor",
    "dagster_msteams.teams_on_run_failure",
    "dagster_pagerduty.pagerduty_resource",
    "dagster_pagerduty.make_pagerduty_on_run_failure_sensor",
    "dagster_pagerduty.pagerduty_on_run_failure",
    "dagster_pandas.PandasColumn",
    "dagster_pandas.PandasParquetIOManager",
    "dagster_polars.PolarsDeltaIOManager",
    "dagster_polars.PolarsParquetIOManager",
    "dagster_shell.shell_command_op",
    "dagster_shell.shell_op",
    "dagster_shell.create_shell_command_op",
    "dagster_shell.create_shell_script_op",
    "dagster_shell.shell_solid",
    "dagster_shell.create_shell_command_solid",
    "dagster_shell.create_shell_script_solid",
    "dagster_slack.SlackResource",
    "dagster_slack.make_slack_on_run_failure_sensor",
    "dagster_slack.make_slack_on_run_success_sensor",
    "dagster_slack.slack_on_run_failure",
    "dagster_slack.slack_on_run_success",
    "dagster_twilio.twilio_resource",
    "dagster_wandb.WandbArtifactConfiguration",
    "dagster_wandb.run_launch_agent",
    "dagster_wandb.run_launch_job",
    "dagstermill.define_dagstermill_op",
    "dagstermill.define_dagstermill_asset",
    "dagstermill.define_dagstermill_solid",
    "dagstermill.DagstermillOpExecutionError",
    "dagstermill.DagstermillExecutionError",
    "dagstermill.ConfigurableLocalNotebookExecutor",
    "dagstermill.local_output_notebook_io_manager",
    # Additional Pipes components documented but missing @public
    "dagster_pipes.PipesParamsLoader",
    "dagster_pipes.PipesEnvVarParamsLoader",
    "dagster_pipes.PipesCliArgsParamsLoader",
    "dagster_pipes.PipesMappingParamsLoader",
    "dagster_pipes.PipesBlobStoreMessageWriter",
    "dagster_pipes.PipesMessageWriterChannel",
    "dagster_pipes.PipesBlobStoreMessageWriterChannel",
    "dagster_pipes.PipesStreamMessageWriterChannel",
    "dagster_pipes.PipesFileMessageWriterChannel",
    "dagster_pipes.PipesS3MessageWriterChannel",
    "dagster_pipes.PipesGCSMessageWriterChannel",
    "dagster_pipes.PipesBufferedFilesystemMessageWriterChannel",
    "dagster_pipes.DagsterPipesError",
    "dagster_pipes.DagsterPipesWarning",
    "dagster_pipes.open_dagster_pipes",
    # Additional dagstermill components
    "dagstermill.ConfigurableLocalOutputNotebookIOManager",
    "dagstermill.DagstermillExecutionContext",
    "dagstermill.DagstermillError",
    # Tableau components exported at top level
    "dagster_tableau.TableauCloudWorkspace",
    "dagster_tableau.TableauServerWorkspace",
    "dagster_tableau.DagsterTableauTranslator",
    "dagster_tableau.load_tableau_asset_specs",
    "dagster_tableau.build_tableau_materializable_assets_definition",
    "dagster_tableau.parse_tableau_external_and_materializable_asset_specs",
    "dagster_tableau.tableau_assets",
    # Airlift components exported at top level
    "dagster_airlift.AirflowInstance",
    "dagster_airlift.AirflowAuthBackend",
    "dagster_airlift.AirflowBasicAuthBackend",
    "dagster_airlift.TaskHandleDict",
    "dagster_airlift.DagInfo",
    "dagster_airlift.AirflowDefinitionsData",
    "dagster_airlift.AirflowInstanceComponent",
    "dagster_airlift.MwaaSessionAuthBackend",
    "dagster_airlift.BaseDagsterAssetsOperator",
    "dagster_airlift.AirflowProxiedState",
    "dagster_airlift.DagProxiedState",
    "dagster_airlift.TaskProxiedState",
    "dagster_airlift.BaseProxyTaskToDagsterOperator",
    "dagster_airlift.DefaultProxyTaskToDagsterOperator",
    "dagster_airlift.BaseProxyDAGToDagsterOperator",
    "dagster_airlift.DefaultProxyDAGToDagsterOperator",
    "dagster_airlift.build_defs_from_airflow_instance",
    "dagster_airlift.assets_with_task_mappings",
    "dagster_airlift.assets_with_dag_mappings",
    "dagster_airlift.proxying_to_dagster",
    "dagster_airlift.load_proxied_state_from_yaml",
    # Azure components exported at top level
    "dagster_azure.blob.AzureBlobComputeLogManager",
    "dagster_azure.adls2.ADLS2FileHandle",
    # Weights & Biases components exported at top level
    "dagster_wandb.SerializationModule",
}

# Modules to exclude from @public scanning
EXCLUDE_MODULES_FROM_PUBLIC_SCAN = set()

# RST files to exclude from symbol extraction
EXCLUDE_RST_FILES = set()
