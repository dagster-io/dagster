import json
from collections.abc import Sequence

import pytest
from dagster import MaterializeResult, build_op_context
from dagster_sling import SlingResource
from dagster_sling.sling_event_iterator import SlingEventIterator
from pydantic import PrivateAttr

STREAM = "file:///data/orders.csv"


class RecordingSlingResource(SlingResource):
    """Records Sling CLI calls instead of running them, and answers every query with a count of 4."""

    _calls: list[list[str]] = PrivateAttr(default_factory=list)

    def run_sling_cli(self, args: Sequence[str], force_json: bool = False) -> str:
        self._calls.append(list(args))
        return json.dumps({"fields": ["ct"], "rows": [[4]]})


@pytest.fixture
def sling() -> RecordingSlingResource:
    return RecordingSlingResource(connections=[])


def fetch_row_count(sling: RecordingSlingResource, inserted_into: str) -> dict:
    sling._stdout = [  # noqa: SLF001
        f"running stream {STREAM}",
        f"inserted 4 rows into {inserted_into} in 0 secs [6 r/s]",
        "",
    ]
    events = SlingEventIterator(
        iter([MaterializeResult(metadata={"stream_name": STREAM})]),
        sling,
        {"target": "SLING_SQLITE"},
        build_op_context(),
    )
    (event,) = list(events.fetch_row_count())
    return dict(event.metadata or {})


def test_row_count_queries_the_logged_table(sling: RecordingSlingResource) -> None:
    metadata = fetch_row_count(sling, '"main"."orders"')

    assert sling._calls == [  # noqa: SLF001
        ["conns", "exec", "SLING_SQLITE", "select count(*) as ct from main.orders"]
    ]
    assert metadata["dagster/row_count"] == 4
    assert metadata["dagster/storage_kind"] == "SLING_SQLITE"


@pytest.mark.parametrize(
    "inserted_into",
    [
        '"main"."orders""; drop table users; --"',
        "main.orders; drop table users",
        "main.orders /* drop table users */",
        "`main`.`orders`; drop table users",
    ],
)
def test_row_count_skips_unsafe_table_names(
    sling: RecordingSlingResource, inserted_into: str
) -> None:
    metadata = fetch_row_count(sling, inserted_into)

    assert not any("drop table" in " ".join(call) for call in sling._calls)  # noqa: SLF001
    assert "dagster/row_count" not in metadata
    assert metadata["stream_name"] == STREAM


def test_row_count_allows_backtick_quoted_names(sling: RecordingSlingResource) -> None:
    metadata = fetch_row_count(sling, "`my-project`.`dataset`.`orders`")

    assert sling._calls == [  # noqa: SLF001
        [
            "conns",
            "exec",
            "SLING_SQLITE",
            "select count(*) as ct from `my-project`.`dataset`.`orders`",
        ]
    ]
    assert metadata["dagster/row_count"] == 4


def test_row_count_allows_non_ascii_names(sling: RecordingSlingResource) -> None:
    metadata = fetch_row_count(sling, '"public"."café"')

    assert sling._calls == [  # noqa: SLF001
        ["conns", "exec", "SLING_SQLITE", "select count(*) as ct from public.café"]
    ]
    assert metadata["dagster/row_count"] == 4
