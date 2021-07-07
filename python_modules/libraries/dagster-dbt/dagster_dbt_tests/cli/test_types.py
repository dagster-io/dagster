import pickle

from dagster_dbt import DbtCliOutput

from ..test_types import DBT_RESULT_DICT


class TestDbtCliOutput:
    def test_init(self):
        dco = DbtCliOutput(
            command="dbt run",
            return_code=0,
            raw_output="The raw output (stdout).",
            result=DBT_RESULT_DICT,
            logs=[],
        )
        assert len(dco.result["results"]) == len(DBT_RESULT_DICT["results"])

    def test_pickle_roundtrip(self):  # pylint: disable=unused-argument
        dco = DbtCliOutput(
            command="dbt run",
            return_code=0,
            raw_output="The raw output (stdout).",
            result=DBT_RESULT_DICT,
            logs=[{"some": {"nested": {"logs"}}}, {"other": "log"}],
        )
        assert vars(pickle.loads(pickle.dumps(dco))) == vars(dco)
