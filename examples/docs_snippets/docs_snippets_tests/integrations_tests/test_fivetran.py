import os

from docs_snippets.integrations.fivetran.fivetran import (
    scope_add_downstream_assets,
    scope_schedule_assets,
)


def test_scope_add_downstream_assets_can_load():
    os.environ["FIVETRAN_API_KEY"] = "foo"
    os.environ["FIVETRAN_API_SECRET"] = "bar"

    scope_add_downstream_assets()


def test_scope_schedule_assets_can_load():
    scope_schedule_assets()
