import pickle

from dagster_dbt.core.types import DbtCliOutput

DBT_RESULT_DICT = {
    "logs": [],
    "results": [
        {
            "unique_id": "model.fake_model",
            "error": None,
            "status": "CREATE VIEW",
            "execution_time": 1.1,
            "thread_id": "Thread-1",
            "timing": [
                {
                    "name": "compile",
                    "started_at": "2020-09-28T17:00:18.426563Z",
                    "completed_at": "2020-09-28T17:00:18.447900Z",
                },
                {
                    "name": "execute",
                    "started_at": "2020-09-28T17:00:18.448162Z",
                    "completed_at": "2020-09-28T17:00:18.521685Z",
                },
            ],
        },
        {
            "unique_id": "model.fake_model_2",
            "error": "This is a test error message on a dbt node.",
            "status": "ERROR",
            "execution_time": 1.1,
            "thread_id": "Thread-2",
            "timing": [],
        },
    ],
    "generated_at": "2020-09-28T17:00:18.746001Z",
    "elapsed_time": 1.1,
}


def test_init():
    dco = DbtCliOutput(
        command="dbt run",
        return_code=0,
        raw_output="The raw output (stdout).",
        result=DBT_RESULT_DICT,
        logs=[],
    )
    assert len(dco.result["results"]) == len(DBT_RESULT_DICT["results"])


def test_pickle_roundtrip():
    dco = DbtCliOutput(
        command="dbt run",
        return_code=0,
        raw_output="The raw output (stdout).",
        result=DBT_RESULT_DICT,
        logs=[{"some": {"nested": {"logs"}}}, {"other": "log"}],
    )
    assert vars(pickle.loads(pickle.dumps(dco))) == vars(dco)
