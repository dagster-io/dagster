from dagster._core.definitions.backfill_policy import BackfillPolicy, BackfillPolicyType


def test_type():
    assert BackfillPolicy.single_run().policy_type == BackfillPolicyType.SINGLE_RUN
    assert BackfillPolicy.multi_run().policy_type == BackfillPolicyType.MULTI_RUN
