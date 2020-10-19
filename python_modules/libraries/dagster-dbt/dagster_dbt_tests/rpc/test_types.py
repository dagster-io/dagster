import pickle

from dagster_dbt import DbtRpcOutput

from ..test_types import DBT_RESULT_DICT

DBT_RPC_RESULT_DICT = {
    **DBT_RESULT_DICT,
    "state": "success",
    "start": "2020-09-28T17:10:56.070900Z",
    "end": "2020-09-28T17:10:58.116186Z",
    "elapsed": 2.045286,
}


class TestDbtRpcOutput:
    def test_from_dict(self):
        dro = DbtRpcOutput.from_dict(DBT_RPC_RESULT_DICT)
        assert len(dro.result) == len(DBT_RPC_RESULT_DICT["results"])

    def test_pickle_roundtrip(self):  # pylint: disable=unused-argument
        dco = DbtRpcOutput.from_dict(DBT_RPC_RESULT_DICT)
        assert pickle.loads(pickle.dumps(dco)) == dco
