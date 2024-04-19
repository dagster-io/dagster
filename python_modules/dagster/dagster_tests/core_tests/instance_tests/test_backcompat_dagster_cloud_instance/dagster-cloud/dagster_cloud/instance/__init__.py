from dagster._core.instance import DagsterInstance, InstanceRef


class DagsterCloudAgentInstance(DagsterInstance):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def config_schema(cls):
        return {}

    @staticmethod
    def config_defaults(base_dir):
        return InstanceRef.config_defaults(base_dir)
