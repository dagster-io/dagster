from docs_snippets.integrations.airbyte.airbyte import (
    scope_add_downstream_assets,
    scope_define_instance,
    scope_schedule_assets,
)


def test_scope_define_instance():
    scope_define_instance()


def test_scope_add_downstream_assets_can_load():
    scope_add_downstream_assets()


def test_scope_schedule_assets_can_load():
    scope_schedule_assets()
