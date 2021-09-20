import pickle

from dagster_dbt import DbtRpcOutput
from mock import MagicMock
from requests import Response

from ..test_types import DBT_RESULT_DICT

DBT_RPC_RESPONSE_DICT = {
    "result": {
        **DBT_RESULT_DICT,
        "state": "success",
        "start": "2020-09-28T17:10:56.070900Z",
        "end": "2020-09-28T17:10:58.116186Z",
        "elapsed": 2.045286,
    },
    "id": "xyz-abc-123-456",
    "jsonrpc": "2.0",
}


def test_attributes():
    response = Response()
    response.json = MagicMock(return_value=DBT_RPC_RESPONSE_DICT)
    dro = DbtRpcOutput(response=response)
    assert len(dro.result["results"]) == len(DBT_RPC_RESPONSE_DICT["result"]["results"])


def test_pickle_roundtrip():
    response = Response()
    response.json = MagicMock(return_value=DBT_RPC_RESPONSE_DICT)
    dro = DbtRpcOutput(response=response)

    dro_new = pickle.loads(pickle.dumps(dro))
    assert dro_new.result == dro.result
    assert dro_new.response_dict == dro.response_dict
    assert dro_new.response.text == dro.response.text
