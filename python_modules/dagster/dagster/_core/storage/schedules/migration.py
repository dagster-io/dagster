from collections.abc import Mapping
from typing import Callable, Optional

import sqlalchemy.exc as db_exc
from tqdm import tqdm

from dagster._core.scheduler.instigation import InstigatorState
from dagster._core.storage.schedules.base import ScheduleStorage
from dagster._core.storage.schedules.schema import InstigatorsTable, JobTable, JobTickTable
from dagster._core.storage.sqlalchemy_compat import db_select
from dagster._serdes import deserialize_value
from dagster._utils import PrintFn

SCHEDULE_JOBS_SELECTOR_ID = "schedule_jobs_selector_id"
SCHEDULE_TICKS_SELECTOR_ID = "schedule_ticks_selector_id"

REQUIRED_SCHEDULE_DATA_MIGRATIONS: Mapping[str, Callable] = {
    SCHEDULE_JOBS_SELECTOR_ID: lambda: add_selector_id_to_jobs_table,
}
OPTIONAL_SCHEDULE_DATA_MIGRATIONS: Mapping[str, Callable] = {
    SCHEDULE_TICKS_SELECTOR_ID: lambda: add_selector_id_to_ticks_table,
}


def add_selector_id_to_jobs_table(
    storage: ScheduleStorage, print_fn: Optional[PrintFn] = None
) -> None:
    """Utility method that calculates the selector_id for each stored instigator state, and writes
    it to the jobs table.
    """
    if print_fn:
        print_fn("Querying storage.")

    with storage.connect() as conn:  # type: ignore
        rows = conn.execute(
            db_select(
                [
                    JobTable.c.id,
                    JobTable.c.job_body,
                    JobTable.c.create_timestamp,
                    JobTable.c.update_timestamp,
                ]
            ).order_by(JobTable.c.id.asc())
        ).fetchall()

        rows_progress = tqdm(rows) if print_fn else rows

        for row_id, state_str, create_timestamp, update_timestamp in rows_progress:
            state = deserialize_value(state_str, InstigatorState)
            selector_id = state.selector_id

            # insert the state into a new instigator table, which has a unique constraint on
            # selector_id
            try:
                conn.execute(
                    InstigatorsTable.insert().values(
                        selector_id=selector_id,
                        repository_selector_id=state.repository_selector_id,
                        status=state.status.value,
                        instigator_type=state.instigator_type.value,
                        instigator_body=state_str,
                        create_timestamp=create_timestamp,
                        update_timestamp=update_timestamp,
                    )
                )
            except db_exc.IntegrityError:
                conn.execute(
                    InstigatorsTable.update()
                    .where(InstigatorsTable.c.selector_id == selector_id)
                    .values(
                        status=state.status.value,
                        repository_selector_id=state.repository_selector_id,
                        instigator_type=state.instigator_type.value,
                        instigator_body=state_str,
                        update_timestamp=update_timestamp,
                    )
                )

            conn.execute(
                JobTable.update()
                .where(JobTable.c.id == row_id)
                .where(JobTable.c.selector_id.is_(None))
                .values(selector_id=state.selector_id)
            )

    if print_fn:
        print_fn("Complete.")


def add_selector_id_to_ticks_table(
    storage: ScheduleStorage, print_fn: Optional[PrintFn] = None
) -> None:
    """Utility method that calculates the selector_id for each stored instigator state, and writes
    it to the jobs table.
    """
    if print_fn:
        print_fn("Querying storage.")

    instigator_states = storage.all_instigator_state()

    states = tqdm(instigator_states) if print_fn else instigator_states

    for state in states:
        with storage.connect() as conn:  # type: ignore
            conn.execute(
                JobTickTable.update()
                .where(JobTickTable.c.job_origin_id == state.instigator_origin_id)
                .where(JobTickTable.c.selector_id.is_(None))
                .values(selector_id=state.selector_id)
            )

    if print_fn:
        print_fn("Complete.")
