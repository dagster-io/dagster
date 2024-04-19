from typing import Any

from dagster._core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster._serdes import (
    ConfigurableClassData,
)


class MockCloudComputeLogStorage(LocalComputeLogManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Any
    ) -> "MockCloudComputeLogStorage":
        return cls(inst_data=inst_data, **config_value)
