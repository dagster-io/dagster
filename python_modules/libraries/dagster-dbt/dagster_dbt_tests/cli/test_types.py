import pickle

from dagster_dbt import DbtCliOutput

from ..test_types import DBT_RESULT_DICT

DBT_CLI_RESULT_DICT = {
    "command": "dbt run",
    "return_code": 0,
    "raw_output": "The raw output (stdout).",
    **DBT_RESULT_DICT,
}

DBT_CLI_RESULT_WITH_STATS_DICT = {
    "num_pass": 1,
    "num_warn": 1,
    "num_error": 1,
    "num_skip": 1,
    "num_total": 4,
    **DBT_CLI_RESULT_DICT,
}


class TestDbtCliOutput:
    def test_from_dict(self):
        dco = DbtCliOutput.from_dict(DBT_CLI_RESULT_DICT)
        assert len(dco.result) == len(DBT_CLI_RESULT_DICT["results"])
        assert dco.num_pass is None
        assert dco.num_warn is None
        assert dco.num_error is None
        assert dco.num_skip is None
        assert dco.num_total is None

    def test_from_dict_with_stats(self):
        dco = DbtCliOutput.from_dict(DBT_CLI_RESULT_WITH_STATS_DICT)
        assert dco.num_pass == DBT_CLI_RESULT_WITH_STATS_DICT["num_pass"]
        assert dco.num_warn == DBT_CLI_RESULT_WITH_STATS_DICT["num_warn"]
        assert dco.num_error == DBT_CLI_RESULT_WITH_STATS_DICT["num_error"]
        assert dco.num_skip == DBT_CLI_RESULT_WITH_STATS_DICT["num_skip"]
        assert dco.num_total == DBT_CLI_RESULT_WITH_STATS_DICT["num_total"]

    def test_pickle_roundtrip(self):  # pylint: disable=unused-argument
        dco = DbtCliOutput.from_dict(DBT_CLI_RESULT_DICT)
        assert pickle.loads(pickle.dumps(dco)) == dco
