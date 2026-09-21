from abc import abstractproperty
from enum import Enum
from typing import Any

from dagster import DagsterError
from pydantic import BaseModel


class AnomalyDetectionError(DagsterError):
    pass


class FreshnessAnomalyDetectionResult(BaseModel):
    last_updated_timestamp: float
    evaluation_timestamp: float
    last_update_time_lower_bound: float
    maximum_acceptable_delta: float
    model_training_range_start_timestamp: float
    model_training_range_end_timestamp: float


class AnomalyDetectionModelVersion(Enum):
    FRESHNESS_BETA = "FRESHNESS_BETA"

    @property
    def minimum_required_records(self) -> int:
        if self == AnomalyDetectionModelVersion.FRESHNESS_BETA:
            return 15
        raise NotImplementedError(f"Minimum required records not implemented for {self}")

    @property
    def minimum_required_records_msg(self) -> str:
        return f"Not enough records found to detect anomalies. Need at least {self.minimum_required_records}."


### INTERNAL MODEL PARAMETER SETS ###


class InternalModelParams(BaseModel):
    @abstractproperty
    def model_version(self) -> AnomalyDetectionModelVersion:
        raise NotImplementedError("Subclasses must implement this method")


class InternalBetaFreshnessAnomalyDetectionParams(InternalModelParams):
    sensitivity: float
    asset_key_user_string: str

    @property
    def model_version(self) -> AnomalyDetectionModelVersion:
        return AnomalyDetectionModelVersion.FRESHNESS_BETA


### USER FACING MODEL PARAMETER SETS ###


class AnomalyDetectionModelParams(BaseModel):
    @abstractproperty
    def model_version(self) -> AnomalyDetectionModelVersion:
        raise NotImplementedError("Subclasses must implement this method")

    @abstractproperty
    def as_metadata(self) -> dict[str, Any]:
        raise NotImplementedError("Subclasses must implement this method")


class BetaFreshnessAnomalyDetectionParams(AnomalyDetectionModelParams):
    sensitivity: float

    @property
    def model_version(self) -> AnomalyDetectionModelVersion:
        return AnomalyDetectionModelVersion.FRESHNESS_BETA

    @property
    def as_metadata(self) -> dict[str, Any]:
        return {
            "sensitivity": self.sensitivity,
        }
