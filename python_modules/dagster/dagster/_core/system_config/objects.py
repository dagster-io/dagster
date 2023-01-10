"""System-provided config objects and constructors."""
from typing import (
    AbstractSet,
    Any,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

import dagster._check as check
from dagster._core.definitions.configurable import ConfigurableDefinition
from dagster._core.definitions.executor_definition import (
    ExecutorDefinition,
    execute_in_process_executor,
)
from dagster._core.definitions.pipeline_definition import PipelineDefinition
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.errors import DagsterInvalidConfigError
from dagster._utils import ensure_single_item


class OpConfig(
    NamedTuple(
        "_OpConfig",
        [
            ("config", object),
            ("inputs", Mapping[str, object]),
            ("outputs", "OutputsConfig"),
        ],
    )
):
    def __new__(cls, config, inputs: Mapping[str, object], outputs: "OutputsConfig"):
        return super(OpConfig, cls).__new__(
            cls,
            config,
            check.opt_mapping_param(inputs, "inputs", key_type=str),
            check.inst_param(outputs, "outputs", OutputsConfig),
        )

    @staticmethod
    def from_dict(config: Mapping[str, Any]) -> "OpConfig":
        check.mapping_param(config, "config", key_type=str)

        return OpConfig(
            config=config.get("config"),
            inputs=config.get("inputs") or {},
            outputs=OutputsConfig(config.get("outputs")),
        )


class OutputsConfig(NamedTuple):
    """
    Outputs are configured as a dict if any of the outputs have an output manager with an
    output_config_schema, and a list otherwise.
    """

    config: Optional[Union[Dict, List]]

    @property
    def output_names(self) -> AbstractSet[str]:
        if isinstance(self.config, list):
            return {key for entry in self.config for key in entry.keys()}
        elif isinstance(self.config, dict):
            return self.config.keys()
        else:
            return set()

    @property
    def type_materializer_specs(self) -> Sequence[object]:
        if isinstance(self.config, list):
            return self.config
        else:
            return []

    def get_output_manager_config(self, output_name) -> object:
        if isinstance(self.config, dict):
            return self.config.get(output_name)
        else:
            return None


class ResourceConfig(NamedTuple):
    config: Any

    @staticmethod
    def from_dict(config):
        check.dict_param(config, "config", key_type=str)

        return ResourceConfig(config=config.get("config"))


class ResolvedRunConfig(
    NamedTuple(
        "_ResolvedRunConfig",
        [
            ("solids", Mapping[str, OpConfig]),
            ("execution", "ExecutionConfig"),
            ("resources", Mapping[str, ResourceConfig]),
            ("loggers", Mapping[str, Mapping[str, object]]),
            ("original_config_dict", Any),
            ("mode", Optional[str]),
            ("inputs", Mapping[str, Any]),
        ],
    )
):
    def __new__(
        cls,
        solids: Optional[Mapping[str, OpConfig]] = None,
        execution: Optional["ExecutionConfig"] = None,
        resources: Optional[Mapping[str, ResourceConfig]] = None,
        loggers: Optional[Mapping[str, Mapping[str, object]]] = None,
        original_config_dict: Optional[Mapping[str, object]] = None,
        mode: Optional[str] = None,
        inputs: Optional[Mapping[str, object]] = None,
    ):
        check.opt_inst_param(execution, "execution", ExecutionConfig)
        check.opt_mapping_param(original_config_dict, "original_config_dict")
        resources = check.opt_mapping_param(resources, "resources", key_type=str)
        check.opt_str_param(mode, "mode")
        inputs = check.opt_mapping_param(inputs, "inputs", key_type=str)

        if execution is None:
            execution = ExecutionConfig(None, None)

        return super(ResolvedRunConfig, cls).__new__(
            cls,
            solids=check.opt_mapping_param(solids, "solids", key_type=str, value_type=OpConfig),
            execution=execution,
            resources=resources,
            loggers=check.opt_mapping_param(loggers, "loggers", key_type=str, value_type=Mapping),
            original_config_dict=original_config_dict,
            mode=mode,
            inputs=inputs,
        )

    @staticmethod
    def build(
        pipeline_def: PipelineDefinition,
        run_config: Optional[Mapping[str, object]] = None,
        mode: Optional[str] = None,
    ) -> "ResolvedRunConfig":
        """This method validates a given run config against the pipeline config schema. If
        successful, we instantiate an ResolvedRunConfig object.

        In case the run_config is invalid, this method raises a DagsterInvalidConfigError
        """
        from dagster._config import process_config

        from .composite_descent import composite_descent

        check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
        run_config = check.opt_mapping_param(run_config, "run_config")
        check.opt_str_param(mode, "mode")

        mode = mode or pipeline_def.get_default_mode_name()
        run_config_schema = pipeline_def.get_run_config_schema(mode)

        if run_config_schema.config_mapping:
            # add user code boundary
            run_config = run_config_schema.config_mapping.resolve_from_unvalidated_config(
                run_config
            )

        config_evr = process_config(
            run_config_schema.run_config_schema_type, check.not_none(run_config)
        )
        if not config_evr.success:
            raise DagsterInvalidConfigError(
                f"Error in config for {pipeline_def.target_type}".format(pipeline_def.name),
                config_evr.errors,
                run_config,
            )

        config_value = cast(Dict[str, Any], config_evr.value)

        mode_def = pipeline_def.get_mode_definition(mode)

        # If using the `execute_in_process` executor, we ignore the execution config value, since it
        # may be pointing to the executor for the job rather than the `execute_in_process` executor.
        if (
            len(mode_def.executor_defs) == 1
            and mode_def.executor_defs[0]  # pylint: disable=comparison-with-callable
            == execute_in_process_executor
        ):
            config_mapped_execution_configs: Optional[Mapping[str, Any]] = {}
        else:
            if pipeline_def.is_job:
                executor_config = config_value.get("execution", {})
                config_mapped_execution_configs = config_map_executor(
                    executor_config, mode_def.executor_defs[0]
                )
            else:
                config_mapped_execution_configs = config_map_objects(
                    config_value,
                    mode_def.executor_defs,
                    "execution",
                    ExecutorDefinition,
                    "executor",
                )

        resource_defs = pipeline_def.get_required_resource_defs_for_mode(mode)
        resource_configs = config_value.get("resources", {})
        config_mapped_resource_configs = config_map_resources(resource_defs, resource_configs)
        config_mapped_logger_configs = config_map_loggers(pipeline_def, config_value, mode)

        node_key = "ops" if pipeline_def.is_job else "solids"
        solid_config_dict = composite_descent(
            pipeline_def, config_value.get(node_key, {}), mode_def.resource_defs
        )
        input_configs = config_value.get("inputs", {})

        return ResolvedRunConfig(
            solids=solid_config_dict,
            execution=ExecutionConfig.from_dict(config_mapped_execution_configs),
            loggers=config_mapped_logger_configs,
            original_config_dict=run_config,
            resources=config_mapped_resource_configs,
            mode=mode,
            inputs=input_configs,
        )

    def to_dict(self) -> Mapping[str, Mapping[str, object]]:
        env_dict: Dict[str, Mapping[str, object]] = {}

        solid_configs: Dict[str, object] = {}
        for solid_name, solid_config in self.solids.items():
            solid_configs[solid_name] = {
                "config": solid_config.config,
                "inputs": solid_config.inputs,
                "outputs": solid_config.outputs.config,
            }

        env_dict["solids"] = solid_configs

        env_dict["execution"] = (
            {self.execution.execution_engine_name: self.execution.execution_engine_config}
            if self.execution.execution_engine_name
            else {}
        )

        env_dict["resources"] = {
            resource_name: {"config": resource_config.config}
            for resource_name, resource_config in self.resources.items()
        }

        env_dict["loggers"] = self.loggers

        return env_dict


def config_map_executor(
    executor_config: Mapping[str, Any],
    executor_def: ExecutorDefinition,
) -> Mapping[str, object]:
    executor_config_evr = executor_def.apply_config_mapping(executor_config)
    if not executor_config_evr.success:
        raise DagsterInvalidConfigError(
            f"Invalid configuration provided for executor '{executor_def.name}'",
            executor_config_evr.errors,
            executor_config,
        )

    return {executor_def.name: executor_config_evr.value}


def config_map_resources(
    resource_defs: Mapping[str, ResourceDefinition],
    resource_configs: Mapping[str, object],
) -> Mapping[str, ResourceConfig]:
    """This function executes the config mappings for resources with respect to ConfigurableDefinition.
    It iterates over resource_defs and looks up the corresponding config because resources need to
    be mapped regardless of whether they receive config from run_config.
    """
    config_mapped_resource_configs = {}
    for resource_key, resource_def in resource_defs.items():
        resource_config = resource_configs.get(resource_key, {})
        resource_config_evr = resource_def.apply_config_mapping(resource_config)
        if not resource_config_evr.success:
            raise DagsterInvalidConfigError(
                "Error in config for resource {}".format(resource_key),
                resource_config_evr.errors,
                resource_config,
            )
        else:
            config_mapped_resource_configs[resource_key] = ResourceConfig.from_dict(
                resource_config_evr.value
            )

    return config_mapped_resource_configs


def config_map_loggers(
    pipeline_def: PipelineDefinition,
    config_value: Mapping[str, Any],
    mode: str,
) -> Mapping[str, Any]:
    """This function executes the config mappings for loggers with respect to ConfigurableDefinition.
    It uses the `loggers` key on the run_config to determine which loggers will be initialized (and
    thus which ones need config mapping) and then iterates over each, looking up the corresponding
    LoggerDefinition in `mode_def.loggers`.

    The following are the cases of run_config and loggers on mode_def that could emerge
    Run Config                                        Loggers on Mode Def    Behavior                                                          Which Loggers Need Config Mapping?
    -------------------------------------             --------------------   --------------------------------------------------------------    -------------------------------------
    {} or {'loggers': <dict or None>}                 []                     default system loggers with default config                        all loggers on run config (empty set)
    {} or {'loggers': <dict or None>}                 [custom_logger, ...]   default system loggers with default config                        all loggers on run config (empty set)
    {'loggers': {'custom_logger': <dict or None>}}    [custom_logger, ...]   use only the loggers listed in run_config                         all loggers on run config
    {'loggers': {'console': <dict or None>}}          []                     use only the loggers listed in run_config (with default defs)     all loggers on run config

    The behavior of `run_config.loggers` as a source of truth for logger selection comes from:
    python_modules/dagster/dagster/_core/execution/context_creation_pipeline.py#create_log_manager
    See that codepath for more info on how the behavior in the above table is implemented. The logic
    in that function is tightly coupled to this one and changes in either path should be confirmed
    in the other.
    """
    mode_def = pipeline_def.get_mode_definition(mode)
    logger_configs = config_value.get("loggers", {})

    config_mapped_logger_configs = {}

    for logger_key, logger_config in logger_configs.items():
        logger_def = mode_def.loggers.get(logger_key)
        if logger_def is None:
            check.failed(f"No logger found for key {logger_key}")

        logger_config_evr = logger_def.apply_config_mapping(logger_config)
        if not logger_config_evr.success:
            raise DagsterInvalidConfigError(
                "Error in config for logger {}".format(logger_key),
                logger_config_evr.errors,
                logger_config,
            )
        else:
            config_mapped_logger_configs[logger_key] = logger_config_evr.value

    return config_mapped_logger_configs


def config_map_objects(
    config_value: Any,
    defs: Sequence[ExecutorDefinition],
    keyed_by: str,
    def_type: Type,
    name_of_def_type: str,
) -> Optional[Mapping[str, Any]]:
    """This function executes the config mappings for executors definitions with respect to
    ConfigurableDefinition. It calls the ensure_single_item macro on the incoming config and then
    applies config mapping to the result and the first executor_def with the same name on
    the mode_def.
    """
    config = config_value.get(keyed_by)

    check.opt_mapping_param(config, "config", key_type=str)
    if not config:
        return None

    obj_name, obj_config = ensure_single_item(config)

    obj_def = next(
        (defi for defi in defs if defi.name == obj_name), None
    )  # obj_defs are stored in a list and we want to find the def matching name
    check.inst(
        obj_def,
        def_type,
        (
            "Could not find a {def_type} definition on the selected mode that matches the "
            '{def_type} "{obj_name}" given in run config'
        ).format(def_type=def_type, obj_name=obj_name),
    )
    obj_def = cast(ConfigurableDefinition, obj_def)

    obj_config_evr = obj_def.apply_config_mapping(obj_config)
    if not obj_config_evr.success:
        raise DagsterInvalidConfigError(
            'Invalid configuration provided for {} "{}"'.format(name_of_def_type, obj_name),
            obj_config_evr.errors,
            obj_config,
        )

    return {obj_name: obj_config_evr.value}


class ExecutionConfig(
    NamedTuple(
        "_ExecutionConfig",
        [
            ("execution_engine_name", Optional[str]),
            ("execution_engine_config", Mapping[str, Any]),
        ],
    )
):
    def __new__(
        cls,
        execution_engine_name: Optional[str],
        execution_engine_config: Optional[Mapping[str, object]],
    ):
        return super(ExecutionConfig, cls).__new__(
            cls,
            execution_engine_name=check.opt_str_param(
                execution_engine_name,
                "execution_engine_name",  # "in_process"
            ),
            execution_engine_config=check.opt_mapping_param(
                execution_engine_config, "execution_engine_config", key_type=str
            ),
        )

    @staticmethod
    def from_dict(config: Optional[Mapping[str, Mapping[str, Any]]] = None) -> "ExecutionConfig":
        config = check.opt_mapping_param(config, "config", key_type=str)
        if config:
            execution_engine_name, execution_engine_config = ensure_single_item(config)
            return ExecutionConfig(
                execution_engine_name, check.is_dict(execution_engine_config).get("config")
            )
        return ExecutionConfig(None, None)
