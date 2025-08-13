"""Test fixtures for run API commands.

These fixtures can be generated from recordings using --record flag.
To update: run commands with --record, review output, then use process_recordings.py script.

Example workflow:
1. dg plus api run view 9d38c7ea --record
2. dg plus api run view nonexistent --record
3. python scripts/process_recordings.py recordings/ this_file.py run_
"""

# Placeholder fixtures - will be replaced by generated ones from recordings

RUN_VIEW_SUCCESS_RESPONSE = {
    "runOrError": {
        "__typename": "Run",
        "id": "abc123def456",
        "runId": "9d38c7ea",
        "status": "SUCCESS",
        "pipelineName": "test_pipeline",
        "jobName": "test_job",
        "creationTime": 1691849429.0,
        "startTime": 1691849431.0,
        "endTime": 1691849506.0,
        "tags": [
            {"key": "test_key", "value": "test_value"},
        ],
        "assets": [
            {"key": {"path": ["test", "asset"]}},
        ],
        "stats": {
            "__typename": "RunStatsSnapshot",
            "id": "stats123",
            "stepsSucceeded": 5,
            "stepsFailed": 0,
            "materializations": 2,
            "expectations": 0,
        },
    }
}

RUN_VIEW_NOT_FOUND_RESPONSE = {
    "runOrError": {
        "__typename": "RunNotFoundError",
        "message": "Run with id 'nonexistent' was not found",
    }
}

RUN_VIEW_ERROR_RESPONSE = {
    "runOrError": {
        "__typename": "PythonError",
        "message": "Database connection failed",
    }
}
