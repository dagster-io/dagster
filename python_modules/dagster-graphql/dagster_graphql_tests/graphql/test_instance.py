from typing import Any

from dagster._core.utils import make_new_run_id
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    GraphQLContextVariant,
    make_graphql_context_test_suite,
)

INSTANCE_QUERY = """
query InstanceDetailSummaryQuery {
    instance {
        runQueuingSupported
        hasInfo
        useAutoMaterializeSensors
        poolConfig {
            poolGranularity
            defaultPoolLimit
            opGranularityRunBuffer
        }
    }
}
"""

GET_CONCURRENCY_LIMITS_QUERY = """
query InstanceConcurrencyLimitsQuery($concurrencyKey: String!) {
    instance {
        concurrencyLimit(concurrencyKey: $concurrencyKey) {
            concurrencyKey
            slotCount
            activeSlotCount
            activeRunIds
            claimedSlots {
                runId
                stepKey
            }
            pendingSteps {
                runId
                stepKey
                enqueuedTimestamp
                assignedTimestamp
                priority
            }
            limit
            usingDefaultLimit
        }
    }
}

"""

ALL_CONCURRENCY_LIMITS_QUERY = """
query AllConcurrencyLimitsQuery {
    instance {
        concurrencyLimits {
            concurrencyKey
            slotCount
            activeSlotCount
            activeRunIds
            claimedSlots {
                runId
                stepKey
            }
            pendingSteps {
                runId
                stepKey
                enqueuedTimestamp
                assignedTimestamp
                priority
            }
            limit
            usingDefaultLimit
        }
    }
}
"""

SET_CONCURRENCY_LIMITS_MUTATION = """
mutation SetConcurrencyLimit($concurrencyKey: String!, $limit: Int!) {
    setConcurrencyLimit(concurrencyKey: $concurrencyKey, limit: $limit)
}
"""

FREE_CONCURRENCY_SLOTS_FOR_RUN_MUTATION = """
mutation FreeConcurrencySlotsForRun($runId: String!) {
    freeConcurrencySlotsForRun(runId: $runId)
}
"""

FREE_CONCURRENCY_SLOTS_MUTATION = """
mutation FreeConcurrencySlots($runId: String!, $stepKey: String) {
    freeConcurrencySlots(runId: $runId, stepKey: $stepKey)
}
"""

BaseTestSuite: Any = make_graphql_context_test_suite(
    context_variants=[
        GraphQLContextVariant.sqlite_with_queued_run_coordinator_managed_grpc_env(),
    ]
)


def fetch_concurrency_limit(graphql_context, key: str):
    results = execute_dagster_graphql(
        graphql_context,
        GET_CONCURRENCY_LIMITS_QUERY,
        {"concurrencyKey": key},
    )
    assert results.data
    assert "instance" in results.data
    assert "concurrencyLimit" in results.data["instance"]
    return results.data["instance"]["concurrencyLimit"]


def set_concurrency_limit(graphql_context, key: str, limit: int):
    execute_dagster_graphql(
        graphql_context,
        SET_CONCURRENCY_LIMITS_MUTATION,
        variables={
            "concurrencyKey": key,
            "limit": limit,
        },
    )


def fetch_all_concurrency_limits(graphql_context):
    results = execute_dagster_graphql(
        graphql_context,
        ALL_CONCURRENCY_LIMITS_QUERY,
    )
    assert results.data
    assert "instance" in results.data
    assert "concurrencyLimits" in results.data["instance"]
    return [limit for limit in results.data["instance"]["concurrencyLimits"]]


class TestInstanceSettings(BaseTestSuite):
    def test_instance_settings(self, graphql_context):
        results = execute_dagster_graphql(graphql_context, INSTANCE_QUERY)
        assert results.data == {
            "instance": {
                "runQueuingSupported": True,
                "hasInfo": graphql_context.show_instance_config,
                "useAutoMaterializeSensors": graphql_context.instance.auto_materialize_use_sensors,
                "poolConfig": {
                    "poolGranularity": None,
                    "defaultPoolLimit": None,
                    "opGranularityRunBuffer": None,
                },
            }
        }

    def test_concurrency_limits(self, graphql_context):
        instance = graphql_context.instance

        # default limits are empty
        all_limits = fetch_all_concurrency_limits(graphql_context)
        assert len(all_limits) == 0

        # set a limit
        set_concurrency_limit(graphql_context, "foo", 10)
        foo = fetch_concurrency_limit(graphql_context, "foo")
        assert foo["concurrencyKey"] == "foo"
        assert foo["slotCount"] == 10
        assert foo["activeSlotCount"] == 0
        assert foo["activeRunIds"] == []
        assert foo["claimedSlots"] == []
        assert foo["pendingSteps"] == []

        # claim a slot
        run_id = make_new_run_id()
        instance.event_log_storage.claim_concurrency_slot("foo", run_id, "fake_step_key")
        foo = fetch_concurrency_limit(graphql_context, "foo")
        assert foo["concurrencyKey"] == "foo"
        assert foo["slotCount"] == 10
        assert foo["activeSlotCount"] == 1
        assert foo["activeRunIds"] == [run_id]
        assert foo["claimedSlots"] == [{"runId": run_id, "stepKey": "fake_step_key"}]
        assert len(foo["pendingSteps"]) == 1
        assert foo["pendingSteps"][0]["runId"] == run_id
        assert foo["pendingSteps"][0]["stepKey"] == "fake_step_key"
        assert foo["pendingSteps"][0]["assignedTimestamp"] is not None
        assert foo["pendingSteps"][0]["priority"] == 0

        set_concurrency_limit(graphql_context, "foo", 5)
        foo = fetch_concurrency_limit(graphql_context, "foo")
        assert foo["concurrencyKey"] == "foo"
        assert foo["slotCount"] == 5
        assert foo["activeSlotCount"] == 1
        assert foo["activeRunIds"] == [run_id]
        assert foo["claimedSlots"] == [{"runId": run_id, "stepKey": "fake_step_key"}]
        assert len(foo["pendingSteps"]) == 1
        assert foo["pendingSteps"][0]["runId"] == run_id
        assert foo["pendingSteps"][0]["stepKey"] == "fake_step_key"
        assert foo["pendingSteps"][0]["assignedTimestamp"] is not None
        assert foo["pendingSteps"][0]["priority"] == 0

        instance.event_log_storage.free_concurrency_slots_for_run(run_id)
        foo = fetch_concurrency_limit(graphql_context, "foo")
        assert foo["concurrencyKey"] == "foo"
        assert foo["slotCount"] == 5
        assert foo["activeSlotCount"] == 0
        assert foo["activeRunIds"] == []
        assert foo["claimedSlots"] == []
        assert foo["pendingSteps"] == []

    def test_concurrency_free(self, graphql_context):
        storage = graphql_context.instance.event_log_storage

        # set a limit
        storage.set_concurrency_slots("foo", 1)

        # claim the slot
        run_id = make_new_run_id()
        run_id_2 = make_new_run_id()
        storage.claim_concurrency_slot("foo", run_id, "fake_step_key")
        # add pending steps
        storage.claim_concurrency_slot("foo", run_id, "fake_step_key_2")
        storage.claim_concurrency_slot("foo", run_id_2, "fake_step_key_3")

        foo_info = storage.get_concurrency_info("foo")
        assert foo_info.slot_count == 1
        assert foo_info.active_slot_count == 1
        assert foo_info.active_run_ids == {run_id}
        assert foo_info.pending_step_count == 2
        assert foo_info.pending_run_ids == {run_id, run_id_2}
        assert foo_info.assigned_step_count == 1
        assert foo_info.assigned_run_ids == {run_id}

        execute_dagster_graphql(
            graphql_context,
            FREE_CONCURRENCY_SLOTS_MUTATION,
            variables={"runId": run_id_2, "stepKey": "fake_step_key_3"},
        )

        foo_info = storage.get_concurrency_info("foo")
        assert foo_info.slot_count == 1
        assert foo_info.active_slot_count == 1
        assert foo_info.active_run_ids == {run_id}
        assert foo_info.pending_step_count == 1
        assert foo_info.pending_run_ids == {run_id}
        assert foo_info.assigned_step_count == 1
        assert foo_info.assigned_run_ids == {run_id}

        execute_dagster_graphql(
            graphql_context,
            FREE_CONCURRENCY_SLOTS_MUTATION,
            variables={"runId": run_id},
        )
        foo_info = storage.get_concurrency_info("foo")
        assert foo_info.slot_count == 1
        assert foo_info.active_slot_count == 0
        assert foo_info.active_run_ids == set()
        assert foo_info.pending_step_count == 0
        assert foo_info.pending_run_ids == set()
        assert foo_info.assigned_step_count == 0
        assert foo_info.assigned_run_ids == set()

    def test_concurrency_free_run(self, graphql_context):
        storage = graphql_context.instance.event_log_storage

        # set a limit
        storage.set_concurrency_slots("foo", 1)

        # claim the slot
        run_id = make_new_run_id()
        run_id_2 = make_new_run_id()
        storage.claim_concurrency_slot("foo", run_id, "fake_step_key")
        # add pending steps
        storage.claim_concurrency_slot("foo", run_id, "fake_step_key_2")
        storage.claim_concurrency_slot("foo", run_id_2, "fake_step_key_3")

        foo_info = storage.get_concurrency_info("foo")
        assert foo_info.slot_count == 1
        assert foo_info.active_slot_count == 1
        assert foo_info.active_run_ids == {run_id}
        assert foo_info.pending_step_count == 2
        assert foo_info.pending_run_ids == {run_id, run_id_2}
        assert foo_info.assigned_step_count == 1
        assert foo_info.assigned_run_ids == {run_id}

        execute_dagster_graphql(
            graphql_context,
            FREE_CONCURRENCY_SLOTS_FOR_RUN_MUTATION,
            variables={"runId": run_id},
        )

        foo_info = storage.get_concurrency_info("foo")
        assert foo_info.slot_count == 1
        assert foo_info.active_slot_count == 0
        assert foo_info.active_run_ids == set()
        assert foo_info.pending_step_count == 0
        assert foo_info.pending_run_ids == set()
        assert foo_info.assigned_step_count == 1
        assert foo_info.assigned_run_ids == {run_id_2}


ConcurrencyTestSuite: Any = make_graphql_context_test_suite(
    context_variants=[
        GraphQLContextVariant.sqlite_with_default_concurrency_managed_grpc_env(),
    ]
)


class TestConcurrencyInstanceSettings(ConcurrencyTestSuite):
    def test_default_concurrency(self, graphql_context):
        # no limits
        all_limits = fetch_all_concurrency_limits(graphql_context)
        assert len(all_limits) == 0

        # default limits are empty
        limit = fetch_concurrency_limit(graphql_context, "foo")
        assert limit is not None
        assert limit["slotCount"] == 0
        assert limit["limit"] == 1
        assert limit["usingDefaultLimit"]

        # set a limit
        set_concurrency_limit(graphql_context, "foo", 0)

        limit = fetch_concurrency_limit(graphql_context, "foo")
        assert limit is not None
        assert limit["slotCount"] == 0
        assert limit["limit"] == 0
        assert not limit["usingDefaultLimit"]

        # instance settings
        results = execute_dagster_graphql(graphql_context, INSTANCE_QUERY)
        assert results.data == {
            "instance": {
                "runQueuingSupported": True,
                "hasInfo": graphql_context.show_instance_config,
                "useAutoMaterializeSensors": graphql_context.instance.auto_materialize_use_sensors,
                "poolConfig": {
                    "poolGranularity": None,
                    "defaultPoolLimit": 1,
                    "opGranularityRunBuffer": None,
                },
            }
        }
