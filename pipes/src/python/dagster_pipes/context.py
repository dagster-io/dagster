from typing import Optional, Any, Dict, List, TypeVar, Callable, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def from_dict(f: Callable[[Any], T], x: Any) -> Dict[str, T]:
    assert isinstance(x, dict)
    return { k: f(v) for (k, v) in x.items() }


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class PartitionKeyRange:
    end: Optional[str]
    start: Optional[str]

    def __init__(self, end: Optional[str], start: Optional[str]) -> None:
        self.end = end
        self.start = start

    @staticmethod
    def from_dict(obj: Any) -> 'PartitionKeyRange':
        assert isinstance(obj, dict)
        end = from_union([from_str, from_none], obj.get("end"))
        start = from_union([from_str, from_none], obj.get("start"))
        return PartitionKeyRange(end, start)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.end is not None:
            result["end"] = from_union([from_str, from_none], self.end)
        if self.start is not None:
            result["start"] = from_union([from_str, from_none], self.start)
        return result


class PartitionTimeWindow:
    end: Optional[str]
    start: Optional[str]

    def __init__(self, end: Optional[str], start: Optional[str]) -> None:
        self.end = end
        self.start = start

    @staticmethod
    def from_dict(obj: Any) -> 'PartitionTimeWindow':
        assert isinstance(obj, dict)
        end = from_union([from_str, from_none], obj.get("end"))
        start = from_union([from_str, from_none], obj.get("start"))
        return PartitionTimeWindow(end, start)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.end is not None:
            result["end"] = from_union([from_str, from_none], self.end)
        if self.start is not None:
            result["start"] = from_union([from_str, from_none], self.start)
        return result


class ProvenanceByAssetKey:
    code_version: Optional[str]
    input_data_versions: Optional[Dict[str, str]]
    is_user_provided: Optional[bool]

    def __init__(self, code_version: Optional[str], input_data_versions: Optional[Dict[str, str]], is_user_provided: Optional[bool]) -> None:
        self.code_version = code_version
        self.input_data_versions = input_data_versions
        self.is_user_provided = is_user_provided

    @staticmethod
    def from_dict(obj: Any) -> 'ProvenanceByAssetKey':
        assert isinstance(obj, dict)
        code_version = from_union([from_str, from_none], obj.get("code_version"))
        input_data_versions = from_union([lambda x: from_dict(from_str, x), from_none], obj.get("input_data_versions"))
        is_user_provided = from_union([from_bool, from_none], obj.get("is_user_provided"))
        return ProvenanceByAssetKey(code_version, input_data_versions, is_user_provided)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.code_version is not None:
            result["code_version"] = from_union([from_str, from_none], self.code_version)
        if self.input_data_versions is not None:
            result["input_data_versions"] = from_union([lambda x: from_dict(from_str, x), from_none], self.input_data_versions)
        if self.is_user_provided is not None:
            result["is_user_provided"] = from_union([from_bool, from_none], self.is_user_provided)
        return result


class Context:
    """The serializable data passed from the orchestration process to the external process. This
    gets wrapped in a PipesContext.
    """
    asset_keys: Optional[List[str]]
    code_version_by_asset_key: Optional[Dict[str, Optional[str]]]
    extras: Optional[Dict[str, Any]]
    job_name: Optional[str]
    partition_key: Optional[str]
    partition_key_range: Optional[PartitionKeyRange]
    partition_time_window: Optional[PartitionTimeWindow]
    provenance_by_asset_key: Optional[Dict[str, Optional[ProvenanceByAssetKey]]]
    retry_number: int
    run_id: str

    def __init__(self, asset_keys: Optional[List[str]], code_version_by_asset_key: Optional[Dict[str, Optional[str]]], extras: Optional[Dict[str, Any]], job_name: Optional[str], partition_key: Optional[str], partition_key_range: Optional[PartitionKeyRange], partition_time_window: Optional[PartitionTimeWindow], provenance_by_asset_key: Optional[Dict[str, Optional[ProvenanceByAssetKey]]], retry_number: int, run_id: str) -> None:
        self.asset_keys = asset_keys
        self.code_version_by_asset_key = code_version_by_asset_key
        self.extras = extras
        self.job_name = job_name
        self.partition_key = partition_key
        self.partition_key_range = partition_key_range
        self.partition_time_window = partition_time_window
        self.provenance_by_asset_key = provenance_by_asset_key
        self.retry_number = retry_number
        self.run_id = run_id

    @staticmethod
    def from_dict(obj: Any) -> 'Context':
        assert isinstance(obj, dict)
        asset_keys = from_union([from_none, lambda x: from_list(from_str, x)], obj.get("asset_keys"))
        code_version_by_asset_key = from_union([from_none, lambda x: from_dict(lambda x: from_union([from_none, from_str], x), x)], obj.get("code_version_by_asset_key"))
        extras = from_union([from_none, lambda x: from_dict(lambda x: x, x)], obj.get("extras"))
        job_name = from_union([from_none, from_str], obj.get("job_name"))
        partition_key = from_union([from_none, from_str], obj.get("partition_key"))
        partition_key_range = from_union([from_none, PartitionKeyRange.from_dict], obj.get("partition_key_range"))
        partition_time_window = from_union([from_none, PartitionTimeWindow.from_dict], obj.get("partition_time_window"))
        provenance_by_asset_key = from_union([from_none, lambda x: from_dict(lambda x: from_union([from_none, ProvenanceByAssetKey.from_dict], x), x)], obj.get("provenance_by_asset_key"))
        retry_number = from_int(obj.get("retry_number"))
        run_id = from_str(obj.get("run_id"))
        return Context(asset_keys, code_version_by_asset_key, extras, job_name, partition_key, partition_key_range, partition_time_window, provenance_by_asset_key, retry_number, run_id)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.asset_keys is not None:
            result["asset_keys"] = from_union([from_none, lambda x: from_list(from_str, x)], self.asset_keys)
        if self.code_version_by_asset_key is not None:
            result["code_version_by_asset_key"] = from_union([from_none, lambda x: from_dict(lambda x: from_union([from_none, from_str], x), x)], self.code_version_by_asset_key)
        result["extras"] = from_union([from_none, lambda x: from_dict(lambda x: x, x)], self.extras)
        if self.job_name is not None:
            result["job_name"] = from_union([from_none, from_str], self.job_name)
        if self.partition_key is not None:
            result["partition_key"] = from_union([from_none, from_str], self.partition_key)
        if self.partition_key_range is not None:
            result["partition_key_range"] = from_union([from_none, lambda x: to_class(PartitionKeyRange, x)], self.partition_key_range)
        if self.partition_time_window is not None:
            result["partition_time_window"] = from_union([from_none, lambda x: to_class(PartitionTimeWindow, x)], self.partition_time_window)
        if self.provenance_by_asset_key is not None:
            result["provenance_by_asset_key"] = from_union([from_none, lambda x: from_dict(lambda x: from_union([from_none, lambda x: to_class(ProvenanceByAssetKey, x)], x), x)], self.provenance_by_asset_key)
        result["retry_number"] = from_int(self.retry_number)
        result["run_id"] = from_str(self.run_id)
        return result


def context_from_dict(s: Any) -> Context:
    return Context.from_dict(s)


def context_to_dict(x: Context) -> Any:
    return to_class(Context, x)
