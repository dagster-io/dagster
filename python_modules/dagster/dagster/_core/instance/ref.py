import os
from typing import Any, Mapping, NamedTuple, Optional, Sequence

import yaml

import dagster._check as check
from dagster._serdes import ConfigurableClassData, class_from_code_pointer, whitelist_for_serdes

from .config import DAGSTER_CONFIG_YAML_FILENAME, dagster_instance_config


def compute_logs_directory(base: str) -> str:
    return os.path.join(base, "storage")


def _runs_directory(base: str) -> str:
    return os.path.join(base, "history", "")


def _event_logs_directory(base: str) -> str:
    return os.path.join(base, "history", "runs", "")


def _schedule_directory(base: str) -> str:
    return os.path.join(base, "schedules")


def configurable_class_data(config_field: Mapping[str, Any]) -> ConfigurableClassData:
    return ConfigurableClassData(
        check.str_elem(config_field, "module"),
        check.str_elem(config_field, "class"),
        yaml.dump(check.opt_dict_elem(config_field, "config"), default_flow_style=False),
    )


def configurable_class_data_or_default(
    config_value: Mapping[str, Any], field_name: str, default: Optional[ConfigurableClassData]
) -> Optional[ConfigurableClassData]:
    return (
        configurable_class_data(config_value[field_name])
        if config_value.get(field_name)
        else default
    )


def configurable_secrets_loader_data(
    config_field: Mapping[str, Any], default: Optional[ConfigurableClassData]
) -> Optional[ConfigurableClassData]:
    if not config_field:
        return default
    elif "custom" in config_field:
        return configurable_class_data(config_field["custom"])
    else:
        return None


def configurable_storage_data(
    config_field: Mapping[str, Any], defaults: Mapping[str, Optional[ConfigurableClassData]]
) -> Sequence[ConfigurableClassData]:
    if not config_field:
        storage_data = check.not_none(defaults.get("storage"))
        run_storage_data = check.not_none(defaults.get("run_storage"))
        event_storage_data = check.not_none(defaults.get("event_log_storage"))
        schedule_storage_data = check.not_none(defaults.get("schedule_storage"))
    elif "postgres" in config_field:
        config_yaml = yaml.dump(config_field["postgres"], default_flow_style=False)
        storage_data = ConfigurableClassData(
            module_name="dagster_postgres",
            class_name="DagsterPostgresStorage",
            config_yaml=config_yaml,
        )
        # for backwards compatibility
        run_storage_data = ConfigurableClassData(
            module_name="dagster_postgres",
            class_name="PostgresRunStorage",
            config_yaml=config_yaml,
        )
        event_storage_data = ConfigurableClassData(
            module_name="dagster_postgres",
            class_name="PostgresEventLogStorage",
            config_yaml=config_yaml,
        )
        schedule_storage_data = ConfigurableClassData(
            module_name="dagster_postgres",
            class_name="PostgresScheduleStorage",
            config_yaml=config_yaml,
        )

    elif "mysql" in config_field:
        config_yaml = yaml.dump(config_field["mysql"], default_flow_style=False)
        storage_data = ConfigurableClassData(
            module_name="dagster_mysql",
            class_name="DagsterMySQLStorage",
            config_yaml=config_yaml,
        )
        # for backwards compatibility
        run_storage_data = ConfigurableClassData(
            module_name="dagster_mysql",
            class_name="MySQLRunStorage",
            config_yaml=config_yaml,
        )
        event_storage_data = ConfigurableClassData(
            module_name="dagster_mysql",
            class_name="MySQLEventLogStorage",
            config_yaml=config_yaml,
        )
        schedule_storage_data = ConfigurableClassData(
            module_name="dagster_mysql",
            class_name="MySQLScheduleStorage",
            config_yaml=config_yaml,
        )

    elif "sqlite" in config_field:
        base_dir = check.str_elem(config_field["sqlite"], "base_dir")
        storage_data = ConfigurableClassData(
            "dagster._core.storage.sqlite_storage",
            "DagsterSqliteStorage",
            yaml.dump({"base_dir": base_dir}, default_flow_style=False),
        )
        run_storage_data = ConfigurableClassData(
            "dagster._core.storage.runs",
            "SqliteRunStorage",
            yaml.dump({"base_dir": _runs_directory(base_dir)}, default_flow_style=False),
        )
        event_storage_data = ConfigurableClassData(
            "dagster._core.storage.event_log",
            "SqliteEventLogStorage",
            yaml.dump({"base_dir": _event_logs_directory(base_dir)}, default_flow_style=False),
        )
        schedule_storage_data = ConfigurableClassData(
            "dagster._core.storage.schedules",
            "SqliteScheduleStorage",
            yaml.dump({"base_dir": _schedule_directory(base_dir)}, default_flow_style=False),
        )

    else:
        storage_data = configurable_class_data(config_field["custom"])
        storage_config_yaml = yaml.dump(
            {
                "module_name": storage_data.module_name,
                "class_name": storage_data.class_name,
                "config_yaml": storage_data.config_yaml,
            },
            default_flow_style=False,
        )
        run_storage_data = ConfigurableClassData(
            "dagster._core.storage.legacy_storage", "LegacyRunStorage", storage_config_yaml
        )
        event_storage_data = ConfigurableClassData(
            "dagster._core.storage.legacy_storage", "LegacyEventLogStorage", storage_config_yaml
        )
        schedule_storage_data = ConfigurableClassData(
            "dagster._core.storage.legacy_storage", "LegacyScheduleStorage", storage_config_yaml
        )

    return [storage_data, run_storage_data, event_storage_data, schedule_storage_data]


@whitelist_for_serdes
class InstanceRef(
    NamedTuple(
        "_InstanceRef",
        [
            ("local_artifact_storage_data", ConfigurableClassData),
            ("compute_logs_data", ConfigurableClassData),
            ("scheduler_data", Optional[ConfigurableClassData]),
            ("run_coordinator_data", Optional[ConfigurableClassData]),
            ("run_launcher_data", Optional[ConfigurableClassData]),
            ("settings", Mapping[str, object]),
            # Required for backwards compatibility, but going forward will be unused by new versions
            # of DagsterInstance, which instead will instead grab the constituent storages from the
            # unified `storage_data`, if it is populated.
            ("run_storage_data", ConfigurableClassData),
            ("event_storage_data", ConfigurableClassData),
            ("schedule_storage_data", ConfigurableClassData),
            ("custom_instance_class_data", Optional[ConfigurableClassData]),
            # unified storage field
            ("storage_data", Optional[ConfigurableClassData]),
            ("secrets_loader_data", Optional[ConfigurableClassData]),
        ],
    )
):
    """Serializable representation of a :py:class:`DagsterInstance`.

    Users should not instantiate this class directly.
    """

    def __new__(
        cls,
        local_artifact_storage_data: ConfigurableClassData,
        compute_logs_data: ConfigurableClassData,
        scheduler_data: Optional[ConfigurableClassData],
        run_coordinator_data: Optional[ConfigurableClassData],
        run_launcher_data: Optional[ConfigurableClassData],
        settings: Mapping[str, object],
        run_storage_data: ConfigurableClassData,
        event_storage_data: ConfigurableClassData,
        schedule_storage_data: ConfigurableClassData,
        custom_instance_class_data: Optional[ConfigurableClassData] = None,
        storage_data: Optional[ConfigurableClassData] = None,
        secrets_loader_data: Optional[ConfigurableClassData] = None,
    ):
        return super(cls, InstanceRef).__new__(
            cls,
            local_artifact_storage_data=check.inst_param(
                local_artifact_storage_data, "local_artifact_storage_data", ConfigurableClassData
            ),
            compute_logs_data=check.inst_param(
                compute_logs_data, "compute_logs_data", ConfigurableClassData
            ),
            scheduler_data=check.opt_inst_param(
                scheduler_data, "scheduler_data", ConfigurableClassData
            ),
            run_coordinator_data=check.opt_inst_param(
                run_coordinator_data, "run_coordinator_data", ConfigurableClassData
            ),
            run_launcher_data=check.opt_inst_param(
                run_launcher_data, "run_launcher_data", ConfigurableClassData
            ),
            settings=check.opt_mapping_param(settings, "settings", key_type=str),
            run_storage_data=check.inst_param(
                run_storage_data, "run_storage_data", ConfigurableClassData
            ),
            event_storage_data=check.inst_param(
                event_storage_data, "event_storage_data", ConfigurableClassData
            ),
            schedule_storage_data=check.inst_param(
                schedule_storage_data, "schedule_storage_data", ConfigurableClassData
            ),
            custom_instance_class_data=check.opt_inst_param(
                custom_instance_class_data,
                "instance_class",
                ConfigurableClassData,
            ),
            storage_data=check.opt_inst_param(storage_data, "storage_data", ConfigurableClassData),
            secrets_loader_data=check.opt_inst_param(
                secrets_loader_data, "secrets_loader_data", ConfigurableClassData
            ),
        )

    @staticmethod
    def config_defaults(base_dir: str) -> Mapping[str, Optional[ConfigurableClassData]]:
        default_run_storage_data = ConfigurableClassData(
            "dagster._core.storage.runs",
            "SqliteRunStorage",
            yaml.dump({"base_dir": _runs_directory(base_dir)}, default_flow_style=False),
        )
        default_event_log_storage_data = ConfigurableClassData(
            "dagster._core.storage.event_log",
            "SqliteEventLogStorage",
            yaml.dump({"base_dir": _event_logs_directory(base_dir)}, default_flow_style=False),
        )
        default_schedule_storage_data = ConfigurableClassData(
            "dagster._core.storage.schedules",
            "SqliteScheduleStorage",
            yaml.dump({"base_dir": _schedule_directory(base_dir)}, default_flow_style=False),
        )

        return {
            "local_artifact_storage": ConfigurableClassData(
                "dagster._core.storage.root",
                "LocalArtifactStorage",
                yaml.dump({"base_dir": base_dir}, default_flow_style=False),
            ),
            "storage": ConfigurableClassData(
                "dagster._core.storage.sqlite_storage",
                "DagsterSqliteStorage",
                yaml.dump({"base_dir": base_dir}, default_flow_style=False),
            ),
            "compute_logs": ConfigurableClassData(
                "dagster._core.storage.local_compute_log_manager",
                "LocalComputeLogManager",
                yaml.dump({"base_dir": compute_logs_directory(base_dir)}, default_flow_style=False),
            ),
            "scheduler": ConfigurableClassData(
                "dagster._core.scheduler",
                "DagsterDaemonScheduler",
                yaml.dump({}),
            ),
            "run_coordinator": ConfigurableClassData(
                "dagster._core.run_coordinator", "DefaultRunCoordinator", yaml.dump({})
            ),
            "run_launcher": ConfigurableClassData(
                "dagster",
                "DefaultRunLauncher",
                yaml.dump({}),
            ),
            # For back-compat, the default is actually set in the secrets_loader property above,
            # so that old clients loading new config don't try to load a class that they
            # don't recognize
            "secrets": None,
            # LEGACY DEFAULTS
            "run_storage": default_run_storage_data,
            "event_log_storage": default_event_log_storage_data,
            "schedule_storage": default_schedule_storage_data,
        }

    @staticmethod
    def from_dir(base_dir, config_filename=DAGSTER_CONFIG_YAML_FILENAME, overrides=None):
        overrides = check.opt_dict_param(overrides, "overrides")
        config_value, custom_instance_class = dagster_instance_config(
            base_dir, config_filename=config_filename, overrides=overrides
        )

        if custom_instance_class:
            config_keys = set(custom_instance_class.config_schema().keys())
            custom_instance_class_config = {
                key: val for key, val in config_value.items() if key in config_keys
            }
            custom_instance_class_data = ConfigurableClassData(
                config_value["instance_class"]["module"],
                config_value["instance_class"]["class"],
                yaml.dump(custom_instance_class_config, default_flow_style=False),
            )
            defaults = custom_instance_class.config_defaults(base_dir)
        else:
            custom_instance_class_data = None
            defaults = InstanceRef.config_defaults(base_dir)

        local_artifact_storage_data = configurable_class_data_or_default(
            config_value, "local_artifact_storage", defaults["local_artifact_storage"]
        )

        compute_logs_data = configurable_class_data_or_default(
            config_value,
            "compute_logs",
            defaults["compute_logs"],
        )

        if (
            config_value.get("run_storage")
            or config_value.get("event_log_storage")
            or config_value.get("schedule_storage")
        ):
            # using legacy config, specifying config for each of the constituent storages, make sure
            # to create a composite storage
            run_storage_data = configurable_class_data_or_default(
                config_value, "run_storage", defaults["run_storage"]
            )
            event_storage_data = configurable_class_data_or_default(
                config_value, "event_log_storage", defaults["event_log_storage"]
            )
            schedule_storage_data = configurable_class_data_or_default(
                config_value, "schedule_storage", defaults["schedule_storage"]
            )
            storage_data = ConfigurableClassData(
                module_name="dagster._core.storage.legacy_storage",
                class_name="CompositeStorage",
                config_yaml=yaml.dump(
                    {
                        "run_storage": {
                            "module_name": run_storage_data.module_name,
                            "class_name": run_storage_data.class_name,
                            "config_yaml": run_storage_data.config_yaml,
                        },
                        "event_log_storage": {
                            "module_name": event_storage_data.module_name,
                            "class_name": event_storage_data.class_name,
                            "config_yaml": event_storage_data.config_yaml,
                        },
                        "schedule_storage": {
                            "module_name": schedule_storage_data.module_name,
                            "class_name": schedule_storage_data.class_name,
                            "config_yaml": schedule_storage_data.config_yaml,
                        },
                    },
                    default_flow_style=False,
                ),
            )

        else:
            [
                storage_data,
                run_storage_data,
                event_storage_data,
                schedule_storage_data,
            ] = configurable_storage_data(config_value.get("storage"), defaults)

        scheduler_data = configurable_class_data_or_default(
            config_value, "scheduler", defaults["scheduler"]
        )

        run_coordinator_data = configurable_class_data_or_default(
            config_value,
            "run_coordinator",
            defaults["run_coordinator"],
        )

        run_launcher_data = configurable_class_data_or_default(
            config_value,
            "run_launcher",
            defaults["run_launcher"],
        )

        secrets_loader_data = configurable_secrets_loader_data(
            config_value.get("secrets"), defaults["secrets"]
        )

        settings_keys = {
            "telemetry",
            "python_logs",
            "run_monitoring",
            "run_retries",
            "code_servers",
            "retention",
            "sensors",
            "schedules",
        }
        settings = {key: config_value.get(key) for key in settings_keys if config_value.get(key)}

        return InstanceRef(
            local_artifact_storage_data=local_artifact_storage_data,
            run_storage_data=run_storage_data,
            event_storage_data=event_storage_data,
            compute_logs_data=compute_logs_data,
            schedule_storage_data=schedule_storage_data,
            scheduler_data=scheduler_data,
            run_coordinator_data=run_coordinator_data,
            run_launcher_data=run_launcher_data,
            settings=settings,
            custom_instance_class_data=custom_instance_class_data,
            storage_data=storage_data,
            secrets_loader_data=secrets_loader_data,
        )

    @staticmethod
    def from_dict(instance_ref_dict):
        def value_for_ref_item(k, v):
            if v is None:
                return None
            if k == "settings":
                return v
            return ConfigurableClassData(*v)

        return InstanceRef(**{k: value_for_ref_item(k, v) for k, v in instance_ref_dict.items()})

    @property
    def local_artifact_storage(self):
        return self.local_artifact_storage_data.rehydrate()

    @property
    def storage(self):
        return self.storage_data.rehydrate() if self.storage_data else None

    @property
    def run_storage(self):
        return self.run_storage_data.rehydrate()

    @property
    def event_storage(self):
        return self.event_storage_data.rehydrate()

    @property
    def schedule_storage(self):
        return self.schedule_storage_data.rehydrate() if self.schedule_storage_data else None

    @property
    def compute_log_manager(self):
        return self.compute_logs_data.rehydrate()

    @property
    def scheduler(self):
        return self.scheduler_data.rehydrate() if self.scheduler_data else None

    @property
    def run_coordinator(self):
        return self.run_coordinator_data.rehydrate() if self.run_coordinator_data else None

    @property
    def run_launcher(self):
        return self.run_launcher_data.rehydrate() if self.run_launcher_data else None

    @property
    def secrets_loader(self):
        # Defining a default here rather than in stored config to avoid
        # back-compat issues when loading the config on older versions where
        # EnvFileLoader was not defined
        return (
            self.secrets_loader_data.rehydrate()
            if self.secrets_loader_data
            else ConfigurableClassData(
                "dagster._core.secrets.env_file",
                "EnvFileLoader",
                yaml.dump({}),
            ).rehydrate()
        )

    @property
    def custom_instance_class(self):
        return (
            class_from_code_pointer(
                self.custom_instance_class_data.module_name,
                self.custom_instance_class_data.class_name,
            )
            if self.custom_instance_class_data
            else None
        )

    @property
    def custom_instance_class_config(self) -> Mapping[str, Any]:
        return (
            self.custom_instance_class_data.config_dict if self.custom_instance_class_data else {}
        )

    def to_dict(self) -> Mapping[str, Any]:
        return self._asdict()
