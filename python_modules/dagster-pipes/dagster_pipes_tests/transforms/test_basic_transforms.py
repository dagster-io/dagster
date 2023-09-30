class FFDataFrame:
    def __init__(self, data):
        self.data = data


class PipesTransform:
    pass


def add_values(df1: FFDataFrame, df2: FFDataFrame) -> FFDataFrame:
    return FFDataFrame(df1.data + df2.data)


def transform_two_fn(one_output: FFDataFrame) -> FFDataFrame:
    return one_output  # deliberate noop


class StoreRequest:
    def __init__(self, asset_key):
        self._asset_key = asset_key

    @property
    def asset_key(self) -> str:
        return self._asset_key


class ReadRequest(StoreRequest): ...


class WriteRequest(StoreRequest): ...


class FFDataFrameStore:
    def __init__(self, base_address, initial_data=None) -> None:
        self.base_address = base_address
        self.data = initial_data or {}

    def _full_address(self, request: StoreRequest) -> str:
        return self.base_address + "/" + request.asset_key

    def read(self, read_request: ReadRequest) -> FFDataFrame:
        return self.data[self._full_address(read_request)]

    def write(self, write_request: WriteRequest, value: FFDataFrame) -> None:
        self.data[self._full_address(write_request)] = value


def test_basic_test() -> None:
    df1 = FFDataFrame(1)
    df2 = FFDataFrame(2)

    assert transform_one_fn(df1, df2).data == 3


from dataclasses import dataclass
from typing import Dict


@dataclass
class TransformParamInfo:
    asset_key: str


@dataclass
class TransformOutput:
    asset_key: str


@dataclass
class TransformInfo:
    input_params: Dict[str, TransformParamInfo]
    output: TransformOutput


from typing import Callable

from typing_extensions import Annotated


def execute_transform(store: FFDataFrameStore, transform_fn: Callable):
    transform_info = get_transform_info_from_annotated_fn(transform_fn)
    input_values = {}
    for param_name, input_param_info in transform_info.input_params.items():
        value = store.read(ReadRequest(input_param_info.asset_key))
        input_values[param_name] = value

    output_value = transform_fn(**input_values)

    store.write(WriteRequest(transform_info.output.asset_key), output_value)


import inspect


def get_transform_param_info_dict(signature) -> Dict[str, TransformParamInfo]:
    param_infos = {}

    for param_name, param in signature.parameters.items():
        param_type = param.annotation
        if (
            param_type is not param.empty
            and hasattr(param_type, "__metadata__")
            and isinstance(param_type.__metadata__[0], TransformParamInfo)
        ):
            param_infos[param_name] = param_type.__metadata__[0]
    return param_infos


def get_transform_output_annotation(signature) -> TransformOutput:
    return_annotation = signature.return_annotation
    if return_annotation is not inspect.Signature.empty:
        if hasattr(return_annotation, "__metadata__") and isinstance(
            return_annotation.__metadata__[0], TransformOutput
        ):
            return return_annotation.__metadata__[0]
    raise Exception("not found")


def get_transform_info_from_annotated_fn(func) -> TransformInfo:
    signature = inspect.signature(func)
    param_infos = get_transform_param_info_dict(signature)
    transform_output = get_transform_output_annotation(signature)
    return TransformInfo(input_params=param_infos, output=transform_output)


def get_initial_state() -> Dict[str, FFDataFrame]:
    return {
        "some_base_address/df1_table": FFDataFrame(1),
        "some_base_address/df2_table": FFDataFrame(2),
    }


def transform_one_fn(
    df1: Annotated[FFDataFrame, TransformParamInfo("df1_table")],
    df2: Annotated[FFDataFrame, TransformParamInfo("df2_table")],
) -> Annotated[FFDataFrame, TransformOutput("df3_table")]:
    return add_values(df1, df2)


def test_with_storage() -> None:
    store = FFDataFrameStore("some_base_address", get_initial_state())

    assert "some_base_address/df3_table" not in store.data
    execute_transform(store, transform_one_fn)
    assert store.data["some_base_address/df3_table"].data == 3


def test_annotation_access() -> None:
    info = get_transform_info_from_annotated_fn(transform_one_fn)
    assert info.output.asset_key == "df3_table"
