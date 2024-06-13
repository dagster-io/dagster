import datetime
from typing import Iterator, Optional, Sequence, Tuple, Union, cast

import pendulum

from dagster import _check as check
from dagster._annotations import experimental
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus

from ...asset_check_spec import AssetCheckKey
from ...asset_checks import AssetChecksDefinition
from ...asset_selection import AssetSelection
from ...decorators import sensor
from ...run_request import RunRequest, SkipReason
from ...sensor_definition import DefaultSensorStatus, SensorDefinition, SensorEvaluationContext
from ..utils import FRESH_UNTIL_METADATA_KEY, ensure_no_duplicate_asset_checks, seconds_in_words

DEFAULT_FRESHNESS_SENSOR_NAME = "freshness_checks_sensor"
MAXIMUM_RUNTIME_SECONDS = 35  # Due to GRPC communications, only allow this sensor to run for 40 seconds before pausing iteration and resuming in the next run. Leave a bit of time for run requests to be processed.
FRESHNESS_SENSOR_DESCRIPTION = """
    This sensor launches execution of freshness checks for the provided assets. The sensor will
    only launch a new execution of a freshness check if the check previously passed, but enough
    time has passed that the check could be overdue again. Once a check has failed, the sensor
    will not launch a new execution until the asset has been updated (which should automatically 
    execute the check). 
    """


@experimental
def build_sensor_for_freshness_checks(
    *,
    freshness_checks: Sequence[AssetChecksDefinition],
    minimum_interval_seconds: Optional[int] = None,
    name: str = DEFAULT_FRESHNESS_SENSOR_NAME,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
) -> SensorDefinition:
    """Builds a sensor which kicks off evaluation of freshness checks.

    This sensor will kick off an execution of a check in the following cases:
    - The check has never been executed before.
    - The check has been executed before, and the previous result was a success, but it is again
    possible for the check to be overdue based on the `dagster/fresh_until_timestamp` metadata
    on the check result.

    Note that we will not execute if:
    - The freshness check has been executed before, and the previous result was a failure. This is
    because whichever run materializes/observes the run to bring the check back to a passing
    state will end up also running the check anyway, so until that run occurs, there's no point
    in evaluating the check.
    - The freshness check has been executed before, and the previous result was a success, but it is
    not possible for the check to be overdue based on the `dagster/fresh_until_timestamp`
    metadata on the check result. Since the check cannot be overdue, we know the check
    result would not change with an additional execution.

    Args:
        freshness_checks (Sequence[AssetChecksDefinition]): The freshness checks to evaluate.
        minimum_interval_seconds (Optional[int]): The duration in seconds between evaluations of the sensor.
        name (Optional[str]): The name of the sensor. Defaults to "freshness_check_sensor", but a
            name may need to be provided in case of multiple calls of this function.
        default_status (Optional[DefaultSensorStatus]): The default status of the sensor. Defaults
            to stopped.

    Returns:
        SensorDefinition: The sensor that kicks off freshness evaluations.
    """
    freshness_checks = check.sequence_param(freshness_checks, "freshness_checks")
    ensure_no_duplicate_asset_checks(freshness_checks)
    check.invariant(
        check.int_param(minimum_interval_seconds, "minimum_interval_seconds") > 0
        if minimum_interval_seconds
        else True,
        "Interval must be a positive integer.",
    )
    check.str_param(name, "name")

    @sensor(
        name=name,
        minimum_interval_seconds=minimum_interval_seconds,
        asset_selection=AssetSelection.checks(*freshness_checks),
        default_status=default_status,
        description=FRESHNESS_SENSOR_DESCRIPTION,
    )
    def the_sensor(context: SensorEvaluationContext) -> Optional[Union[RunRequest, SkipReason]]:
        left_off_asset_check_key = (
            AssetCheckKey.from_user_string(context.cursor) if context.cursor else None
        )
        start_time = pendulum.now("UTC")
        checks_to_evaluate = []
        checks_iter = freshness_checks_get_evaluations_iter(
            context=context,
            start_time=start_time,
            left_off_asset_check_key=left_off_asset_check_key,
            freshness_checks=freshness_checks,
        )
        # We evaluate checks using an iterator which yields back control to the main loop every
        # iteration; this allows us to pause the sensor if it runs into the maximum runtime.
        check_key, should_evaluate = next(checks_iter, (None, False))
        while (
            pendulum.now("UTC").timestamp() - start_time.timestamp() < MAXIMUM_RUNTIME_SECONDS
            and check_key
        ):
            if should_evaluate:
                checks_to_evaluate.append(check_key)
            check_key, should_evaluate = next(checks_iter, (None, False))
        new_cursor = check_key.to_user_string() if check_key else None
        context.update_cursor(new_cursor)
        if checks_to_evaluate:
            return RunRequest(asset_check_keys=checks_to_evaluate)
        else:
            return SkipReason(
                "No freshness checks need to be evaluated at this time, since all checks are either currently evaluating, have failed, or are not yet overdue."
            )

    return the_sensor


def ordered_iterator_freshness_checks_starting_with_key(
    left_off_asset_check_key: Optional[AssetCheckKey],
    freshness_checks: Sequence[AssetChecksDefinition],
) -> Iterator[AssetCheckKey]:
    asset_check_keys_sorted = sorted(
        [
            asset_check_spec.key
            for asset_check in freshness_checks
            for asset_check_spec in asset_check.check_specs
        ],
        key=lambda key: key.to_user_string(),
    )
    # Offset based on the left off asset check key, but then iterate back through the beginning afterwards
    if left_off_asset_check_key:
        left_off_idx = asset_check_keys_sorted.index(left_off_asset_check_key)
        yield from asset_check_keys_sorted[left_off_idx + 1 :]
        yield from asset_check_keys_sorted[: left_off_idx + 1]
    else:
        yield from asset_check_keys_sorted


def freshness_checks_get_evaluations_iter(
    context: SensorEvaluationContext,
    start_time: datetime.datetime,
    left_off_asset_check_key: Optional[AssetCheckKey],
    freshness_checks: Sequence[AssetChecksDefinition],
) -> Iterator[Tuple[AssetCheckKey, bool]]:
    """Yields the set of freshness check keys to evaluate."""
    for check_key in ordered_iterator_freshness_checks_starting_with_key(
        left_off_asset_check_key, freshness_checks
    ):
        summary_record = context.instance.event_log_storage.get_asset_check_summary_records(
            [check_key]
        )[check_key]
        # Case 1: We have never run the check before. We should run it.
        if summary_record.last_check_execution_record is None:
            context.log.info(
                f"Freshness check {check_key.to_user_string()} has never been executed before. "
                "Adding to run request."
            )
            yield check_key, True
            continue

        # Case 2: The check is currently evaluating. We shouldn't kick off another evaluation until it's done.
        if (
            summary_record.last_check_execution_record.status
            == AssetCheckExecutionRecordStatus.PLANNED
        ):
            context.log.info(
                f"Freshness check on asset {check_key.asset_key.to_user_string()} is in the planned state, indicating it is currently evaluating. Skipping..."
            )
            yield check_key, False
            continue

        evaluation = check.not_none(
            summary_record.last_check_execution_record.event
        ).asset_check_evaluation
        # Case 3: The check previously failed. We shouldn't kick off another evaluation until the asset has been updated.
        if not evaluation or not evaluation.passed:
            context.log.info(
                f"Freshness check {check_key.to_user_string()} failed its last evaluation. Waiting "
                "to re-evaluate until the asset has received an update."
            )
            yield check_key, False
            continue
        # Case 4: The check previously passed. We should re-evaluate if it's possible for the check to be overdue again.
        next_deadline = cast(float, evaluation.metadata[FRESH_UNTIL_METADATA_KEY].value)
        if next_deadline < start_time.timestamp():
            context.log.info(
                f"Freshness check {check_key.to_user_string()} previously passed, but "
                "enough time has passed that it can be overdue again. Adding to run request."
            )
            yield check_key, True
            continue
        else:
            how_long_until_next_deadline = next_deadline - start_time.timestamp()
            context.log.info(
                f"Freshness check {check_key.to_user_string()} previously passed, but "
                f"cannot be overdue again until {seconds_in_words(how_long_until_next_deadline)} from now. Skipping..."
            )
            yield check_key, False
            continue
