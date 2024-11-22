import json
import os
from dataclasses import asdict, dataclass
from hashlib import sha256
from time import sleep
from typing import AbstractSet, Any, Mapping, Optional, Union

from typing_extensions import TypedDict

# For source assets
_DUMMY_VALUE = 100

# ExternalSystem simulates source assets outside of Dagster's control by idempotently creating a set
# of them using dummy data whenever it is constructed.
_SOURCE_ASSETS: Mapping[str, Any] = {
    "delta": _DUMMY_VALUE,
}


class AssetInfo(TypedDict):
    key: str
    code_version: str
    dependencies: AbstractSet[str]


class SourceAssetInfo(TypedDict):
    key: str


class ProvenanceSpec(TypedDict):
    code_version: str
    input_data_versions: Mapping[str, str]


class MaterializeResult(TypedDict):
    data_version: str
    is_memoized: bool


class ObserveResult(TypedDict):
    data_version: str


class ExternalSystem:
    def __init__(self, storage_path: str):
        self._db = _Database(storage_path)

    def materialize(
        self, asset_spec: AssetInfo, provenance_spec: Optional[ProvenanceSpec]
    ) -> MaterializeResult:
        """Recompute an asset if its provenance is missing or stale.

        Receives asset provenance info from Dagster representing the last materialization on record.
        The provenance is compared to the specified code version and current data versions of
        dependencies to determine whether something has changed and the asset should be recomputed.

        Args:
            asset_spec (AssetInfo):
                A dictionary containing an asset key, code version, and data dependencies.
            provenance_spec (ProvenanceSpec):
                A dictionary containing provenance info for the last materialization of the
                specified asset. `None` if there is no materialization on record for the asset.

        Returns (MaterializeResult):
            A dictionary containing the data version for the asset and a boolean flag indicating
            whether the data version corresponds to a memoized value (true) or a freshly computed
            value (false).
        """
        key = asset_spec["key"]
        if (
            not self._db.has(key)
            or provenance_spec is None
            or self._is_provenance_stale(asset_spec, provenance_spec)
        ):
            inputs = {dep: self._db.get(dep).value for dep in asset_spec["dependencies"]}
            value = _compute_value(key, inputs, asset_spec["code_version"])
            data_version = _get_hash(value)
            record = _DatabaseRecord(value, data_version)
            self._db.set(key, record)
            is_memoized = False
        else:
            record = self._db.get(key)
            is_memoized = True
        return {"data_version": record.data_version, "is_memoized": is_memoized}

    def observe(self, asset_spec: Union[AssetInfo, SourceAssetInfo]) -> ObserveResult:
        """Observe an asset or source asset, returning its current data version.

        Args:
            asset_spec (Union[AssetInfo, SourceAssetInfo]):
                A dictionary containing an asset key.

        Returns (ObserveResult):
            A dictionary containing the current data version of the asset.
        """
        return {"data_version": self._db.get(asset_spec["key"]).data_version}

    def _is_provenance_stale(self, asset_spec: AssetInfo, provenance_spec: ProvenanceSpec) -> bool:
        # did code change?
        if provenance_spec["code_version"] != asset_spec["code_version"]:
            return True
        # was a dependency added or removed?
        if set(provenance_spec["input_data_versions"].keys()) != asset_spec["dependencies"]:
            return True
        # did the version of a dependency change?
        for dep_key, version in provenance_spec["input_data_versions"].items():
            if self._db.get(dep_key).data_version != version:
                return True
        return False


def _compute_value(key: str, inputs: Mapping[str, Any], code_version: str) -> Any:
    if code_version != "lib/v1":
        raise Exception(f"Unknown code version {code_version}. Cannot compute.")
    if key == "alpha":
        return 1
    elif key == "beta":
        sleep(10)
        value = inputs["alpha"] + 1
        return value
    elif key == "epsilon":
        sleep(10)
        return inputs["delta"] * 5


def _get_hash(value: Any) -> str:
    hash_sig = sha256()
    hash_sig.update(bytearray(str(value), "utf8"))
    return hash_sig.hexdigest()[:6]


@dataclass
class _DatabaseRecord:
    value: Any
    data_version: str


class _Database:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        if not os.path.exists(self.storage_path):
            os.mkdir(self.storage_path)
        for k, v in _SOURCE_ASSETS.items():
            path = self.asset_path(k)
            if not os.path.exists(path):
                with open(self.asset_path(k), "w") as fd:  # source asset
                    record = _DatabaseRecord(v, _get_hash(v))
                    fd.write(json.dumps(asdict(record)))

    def asset_path(self, key: str) -> str:
        return f"{self.storage_path}/{key}.json"

    def get(self, key: str) -> _DatabaseRecord:
        with open(self.asset_path(key)) as fd:
            return _DatabaseRecord(**json.load(fd))

    def has(self, key: str) -> bool:
        return os.path.exists(self.asset_path(key))

    def set(self, key: str, record: _DatabaseRecord) -> None:
        with open(self.asset_path(key), "w") as fd:
            fd.write(json.dumps(asdict(record)))
