# Contains mode, resources, loggers
from typing import NamedTuple, Optional, Sequence

import dagster._check as check
from dagster._config import ConfigFieldSnap, snap_from_field
from dagster._core.definitions import LoggerDefinition, ResourceDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._serdes import whitelist_for_serdes


def build_mode_def_snap(job_def: JobDefinition) -> "ModeDefSnap":
    from dagster._core.host_representation.external_data import DEFAULT_MODE_NAME

    check.inst_param(job_def, "job_def", JobDefinition)

    root_config_key = job_def.run_config_schema.config_type.key
    return ModeDefSnap(
        name=DEFAULT_MODE_NAME,
        description=None,
        resource_def_snaps=sorted(
            [build_resource_def_snap(name, rd) for name, rd in job_def.resource_defs.items()],
            key=lambda item: item.name,
        ),
        logger_def_snaps=sorted(
            [build_logger_def_snap(name, ld) for name, ld in job_def.loggers.items()],
            key=lambda item: item.name,
        ),
        root_config_key=root_config_key,
    )


@whitelist_for_serdes
class ModeDefSnap(
    NamedTuple(
        "_ModeDefSnap",
        [
            ("name", str),
            ("description", Optional[str]),
            ("resource_def_snaps", Sequence["ResourceDefSnap"]),
            ("logger_def_snaps", Sequence["LoggerDefSnap"]),
            ("root_config_key", Optional[str]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        description: Optional[str],
        resource_def_snaps: Sequence["ResourceDefSnap"],
        logger_def_snaps: Sequence["LoggerDefSnap"],
        root_config_key: Optional[str] = None,
    ):
        return super(ModeDefSnap, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            description=check.opt_str_param(description, "description"),
            resource_def_snaps=check.sequence_param(
                resource_def_snaps, "resource_def_snaps", of_type=ResourceDefSnap
            ),
            logger_def_snaps=check.sequence_param(
                logger_def_snaps, "logger_def_snaps", of_type=LoggerDefSnap
            ),
            root_config_key=check.opt_str_param(root_config_key, "root_config_key"),
        )


def build_resource_def_snap(name, resource_def):
    check.str_param(name, "name")
    check.inst_param(resource_def, "resource_def", ResourceDefinition)
    return ResourceDefSnap(
        name=name,
        description=resource_def.description,
        config_field_snap=snap_from_field("config", resource_def.config_field)
        if resource_def.has_config_field
        else None,
    )


@whitelist_for_serdes
class ResourceDefSnap(
    NamedTuple(
        "_ResourceDefSnap",
        [
            ("name", str),
            ("description", Optional[str]),
            ("config_field_snap", Optional[ConfigFieldSnap]),
        ],
    )
):
    def __new__(
        cls, name: str, description: Optional[str], config_field_snap: Optional[ConfigFieldSnap]
    ):
        return super(ResourceDefSnap, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            description=check.opt_str_param(description, "description"),
            config_field_snap=check.opt_inst_param(
                config_field_snap, "config_field_snap", ConfigFieldSnap
            ),
        )


def build_logger_def_snap(name, logger_def):
    check.str_param(name, "name")
    check.inst_param(logger_def, "logger_def", LoggerDefinition)
    return LoggerDefSnap(
        name=name,
        description=logger_def.description,
        config_field_snap=snap_from_field("config", logger_def.config_field)
        if logger_def.has_config_field
        else None,
    )


@whitelist_for_serdes
class LoggerDefSnap(
    NamedTuple(
        "_LoggerDefSnap",
        [
            ("name", str),
            ("description", Optional[str]),
            ("config_field_snap", Optional[ConfigFieldSnap]),
        ],
    )
):
    def __new__(
        cls, name: str, description: Optional[str], config_field_snap: Optional[ConfigFieldSnap]
    ):
        return super(LoggerDefSnap, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            description=check.opt_str_param(description, "description"),
            config_field_snap=check.opt_inst_param(
                config_field_snap, "config_field_snap", ConfigFieldSnap
            ),
        )
