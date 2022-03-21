from typing import Callable, Mapping

from tqdm import tqdm

from ..schedules.schema import JobTickTable

SCHEDULE_JOBS_SELECTOR_ID = "schedule_jobs_selector_id"
SCHEDULE_TICKS_SELECTOR_ID = "schedule_ticks_selector_id"

REQUIRED_SCHEDULE_DATA_MIGRATIONS: Mapping[str, Callable] = {
    SCHEDULE_JOBS_SELECTOR_ID: lambda: add_selector_id_to_jobs_table,
}
OPTIONAL_SCHEDULE_DATA_MIGRATIONS: Mapping[str, Callable] = {
    SCHEDULE_TICKS_SELECTOR_ID: lambda: add_selector_id_to_ticks_table,
}


def add_selector_id_to_jobs_table(storage, print_fn=None):
    """
    Utility method that calculates the selector_id for each stored instigator state, and writes
    it to the jobs table.
    """

    if print_fn:
        print_fn("Querying storage.")

    instigator_states = storage.all_instigator_state()
    for state in tqdm(instigator_states):
        # should write the selector_id to the jobs table
        storage.update_instigator_state(state)

    if print_fn:
        print_fn("Complete.")


def add_selector_id_to_ticks_table(storage, print_fn=None):
    """
    Utility method that calculates the selector_id for each stored instigator state, and writes
    it to the jobs table.
    """

    if print_fn:
        print_fn("Querying storage.")

    instigator_states = storage.all_instigator_state()
    for state in tqdm(instigator_states):
        selector_id = state.get_selector_id()

        with storage.connect() as conn:
            conn.execute(
                JobTickTable.update()  # pylint: disable=no-value-for-parameter
                .where(JobTickTable.c.job_origin_id == state.instigator_origin_id)
                .values(selector_id=selector_id)
            )

    if print_fn:
        print_fn("Complete.")
