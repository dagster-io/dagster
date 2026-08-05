ERROR_FRAGMENT = """
fragment errorFragment on PythonError {
  message
  className
  stack
  cause {
    message
    className
    stack
    cause {
      message
      className
      stack
    }
  }
}
"""

RUN_ROW_FRAGMENT = """
fragment runRecordFragment on RunRecord {
    storageId
    serializedPipelineRun
    createTimestamp
    updateTimestamp
    startTime
    endTime
}
"""

ADD_RUN_MUTATION = (
    ERROR_FRAGMENT
    + """
    mutation addRunMutation($serializedPipelineRun: String!) {
        runs {
            addRun(serializedPipelineRun: $serializedPipelineRun) {
                ok
                error {
                    ...errorFragment
                }
            }
        }
    }
"""
)

ADD_HISTORICAL_RUN_MUTATION = (
    ERROR_FRAGMENT
    + """
    mutation addHistoricalRunMutation($serializedPipelineRun: String!, $runCreationTime: Float!) {
        runs {
            addHistoricalRun(serializedPipelineRun: $serializedPipelineRun, runCreationTime: $runCreationTime) {
                ok
                error {
                    ...errorFragment
                }
            }
        }
    }
    """
)

GET_RUNS_QUERY = """
    query getRunsQuery($filters: RunsFilter, $cursor: String, $limit: Int, $bucketBy: RunBucket, $ascending: Boolean) {
        runs {
            getRuns(filters: $filters, cursor: $cursor, limit: $limit, bucketBy: $bucketBy, ascending: $ascending)
        }
    }
"""

GET_RUN_IDS_QUERY = """
    query getRunsIdsQuery($filters: RunsFilter, $cursor: String, $limit: Int) {
        runs {
            getRunIds(filters: $filters, cursor: $cursor, limit: $limit)
        }
    }
"""

GET_RUNS_COUNT_QUERY = """
    query getRunsCountQuery($filters: RunsFilter) {
        runs {
            getRunsCount(filters: $filters)
        }
    }
"""

GET_RUN_BY_ID_QUERY = """
    query getRunByIdQuery($runId: String!) {
        runs {
            getRunById(runId: $runId)
        }
    }
"""

HAS_RUN_QUERY = """
    query hasRunQuery($runId: String!) {
        runs {
            hasRun(runId: $runId)
        }
    }
"""

HAS_PIPELINE_SNAPSHOT_QUERY = """
    query hasPipelineSnapshotQuery($pipelineSnapshotId: String!) {
        runs {
            hasPipelineSnapshot(pipelineSnapshotId: $pipelineSnapshotId)
        }
    }
"""

GET_PIPELINE_SNAPSHOT_QUERY = """
    query getPipelineSnapshotQuery($pipelineSnapshotId: String!) {
        runs {
            getPipelineSnapshot(pipelineSnapshotId: $pipelineSnapshotId)
        }
    }
"""

GET_RUN_GROUP_QUERY = """
    query getRunGroupQuery($runId: String!) {
        runs {
            getRunGroupOrError(runId: $runId) {
                __typename
                ... on SerializedRunGroup {
                  rootRunId
                  serializedRuns
                }
                ... on PipelineRunNotFoundError {
                    runId
                }
            }
        }
    }
"""


GET_RUN_RECORDS_QUERY = (
    RUN_ROW_FRAGMENT
    + """
    query getRunRecordsQuery($filters: RunsFilter, $limit: Int, $orderBy: String, $ascending: Boolean, $cursor: String, $bucketBy: RunBucket) {
        runs {
            getRunRecords(filters: $filters, limit: $limit, orderBy: $orderBy, ascending: $ascending, cursor: $cursor, bucketBy: $bucketBy) {
                ...runRecordFragment
            }
        }
    }
"""
)

GET_RUN_TAGS_QUERY = """
    query getRunTagsQuery($jsonTagKeys: JSONString!, $valuePrefix: String, $limit: Int) {
        runs {
            getRunTags(jsonTagKeys: $jsonTagKeys, valuePrefix: $valuePrefix, limit: $limit) {
                key
                values
            }
        }
    }
"""

GET_RUN_TAG_KEYS_QUERY = """
    query getRunTagKeysQuery {
        runs {
            getRunTagKeys
        }
    }
"""


ADD_RUN_TAGS_MUTATION = """
    mutation addRunTagsMutation($runId: String!, $jsonNewTags: JSONString!) {
        runs {
            addRunTags(runId: $runId, jsonNewTags: $jsonNewTags) {
                ok
            }
        }
    }
"""

ADD_PIPELINE_SNAPSHOT_MUTATION = """
    mutation addPipelineSnapshotMutation($serializedPipelineSnapshot: String!, $snapshotId: String) {
        runs {
            addPipelineSnapshot(serializedPipelineSnapshot: $serializedPipelineSnapshot, snapshotId: $snapshotId) {
                ok
            }
        }
    }
"""

HAS_EXECUTION_PLAN_SNAPSHOT_QUERY = """
    query hasExecutionPlanSnapshotQuery($executionPlanSnapshotId: String!) {
        runs {
            hasExecutionPlanSnapshot(executionPlanSnapshotId: $executionPlanSnapshotId)
        }
    }
"""

ADD_EXECUTION_PLAN_SNAPSHOT_MUTATION = """
    mutation addExecutionPlanSnapshotMutation($serializedExecutionPlanSnapshot: String!, $snapshotId: String) {
        runs {
            addExecutionPlanSnapshot(serializedExecutionPlanSnapshot: $serializedExecutionPlanSnapshot, snapshotId: $snapshotId) {
                ok
                snapshotId
            }
        }
    }
"""

GET_EXECUTION_PLAN_SNAPSHOT_QUERY = """
    query getExecutionPlanSnapshotQuery($executionPlanSnapshotId: String!) {
        runs {
            getExecutionPlanSnapshot(executionPlanSnapshotId: $executionPlanSnapshotId)
        }
    }
"""

ADD_DAEMON_HEARTBEAT_MUTATION = """
    mutation addDaemonHeartbeat($serializedDaemonHeartbeat: String!) {
        runs {
            addDaemonHeartbeat(serializedDaemonHeartbeat: $serializedDaemonHeartbeat) {
                ok
            }
        }
    }
"""

GET_DAEMON_HEARTBEATS_QUERY = """
    query getDaemonHeartbeatsQuery {
        runs {
            getDaemonHeartbeats
        }
    }
"""

ADD_RUN_TELEMETRY_MUTATION = """
    mutation addRunTelemetry($serializedTelemetry: String!, $serializedTags: String!) {
        runs {
            addRunTelemetry(serializedTelemetry: $serializedTelemetry, serializedTags: $serializedTags) {
                ok
            }
        }
    }
"""

GET_BACKFILLS_QUERY = """
    query getBackfillsQuery($status: String, $cursor: String, $limit: Int, $filters: BulkActionsFilter) {
        runs {
            getBackfills(status: $status, cursor: $cursor, limit: $limit, filters: $filters)
        }
    }
"""

GET_BACKFILL_QUERY = """
    query getBackfillQuery($backfillId: String!) {
        runs {
            getBackfill(backfillId: $backfillId)
        }
    }
"""

ADD_BACKFILL_MUTATION = """
    mutation addBackfill($serializedPartitionBackfill: String!) {
        runs {
            addBackfill(serializedPartitionBackfill: $serializedPartitionBackfill) {
                ok
            }
        }
    }
"""

UPDATE_BACKFILL_MUTATION = """
    mutation updateBackfill($serializedPartitionBackfill: String!) {
        runs {
            updateBackfill(serializedPartitionBackfill: $serializedPartitionBackfill) {
                ok
            }
        }
    }
"""

GET_RUN_PARTITION_DATA_QUERY = """
    query getRunPartitionData($runsFilter: RunsFilter!) {
        runs {
            getRunPartitionData(runsFilter: $runsFilter)
        }
    }
"""

MUTATE_JOB_ORIGIN = """
    mutation mutateJobOrigin($runId: String!, $serializedJobOrigin: String!) {
        runs {
            mutateJobOrigin(runId: $runId, serializedJobOrigin: $serializedJobOrigin) {
                ok
            }
        }
    }
"""
