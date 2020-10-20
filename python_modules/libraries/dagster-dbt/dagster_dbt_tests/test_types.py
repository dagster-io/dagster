import pickle

from dagster_dbt import DbtResult

DBT_RESULT_DICT = {
    "logs": [],
    "results": [
        {
            "node": {},
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
            "node": {},
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


class TestRunResult:
    def test_from_dict(self):
        rr = DbtResult.from_dict(DBT_RESULT_DICT)
        assert len(rr) == len(DBT_RESULT_DICT["results"])

    def test_pickle_roundtrip(self):  # pylint: disable=unused-argument
        rr = DbtResult.from_dict(DBT_RESULT_DICT)
        assert pickle.loads(pickle.dumps(rr)) == rr
