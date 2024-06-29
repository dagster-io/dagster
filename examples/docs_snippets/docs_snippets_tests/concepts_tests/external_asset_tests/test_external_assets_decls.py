import docs_snippets.concepts.assets.external_assets.external_asset_deps
import docs_snippets.concepts.assets.external_assets.normal_asset_depending_on_external
import docs_snippets.concepts.assets.external_assets.single_declaration
from dagster import AssetKey, Definitions


def test_docs_snippets_concepts_external_asset_single_decl() -> None:
    single_decl_defs: Definitions = (
        docs_snippets.concepts.assets.external_assets.single_declaration.defs
    )
    assert single_decl_defs.get_asset_graph().has(AssetKey("file_in_s3"))


def test_docs_snippets_concepts_external_asset_external_asset_deps() -> None:
    defs_with_deps: Definitions = (
        docs_snippets.concepts.assets.external_assets.external_asset_deps.defs
    )
    assert defs_with_deps.get_asset_graph().has(AssetKey("raw_logs"))
    assert defs_with_deps.get_asset_graph().has(AssetKey("processed_logs"))
    assert defs_with_deps.get_asset_graph().get(
        AssetKey("processed_logs")
    ).parent_keys == {AssetKey("raw_logs")}


def test_docs_snippets_normal_assets_dep_on_external() -> None:
    defs: Definitions = docs_snippets.concepts.assets.external_assets.normal_asset_depending_on_external.defs

    from docs_snippets.concepts.assets.external_assets.normal_asset_depending_on_external import (
        aggregated_logs,
    )

    al_key = aggregated_logs.key

    assert defs.get_asset_graph().has(al_key)
    assert defs.get_asset_graph().get(al_key).parent_keys == {
        AssetKey("processed_logs")
    }

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(asset_selection=[al_key])
        .success
    )
