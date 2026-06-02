import time

import dagster as dg
from dagster._core.pipes.context import PIPES_COMPOSITE_WRITERS_KEY
from dagster._core.pipes.utils import (
    PipesCompositeMessageReader,
    PipesTempFileContextInjector,
    PipesTempFileMessageReader,
    open_pipes_session,
)
from dagster_pipes import (
    DAGSTER_PIPES_CONTEXT_ENV_VAR,
    DAGSTER_PIPES_MESSAGES_ENV_VAR,
    PipesContext,
    PipesMappingParamsLoader,
    open_dagster_pipes,
)

# ########################
# ##### TESTS
# ########################


def test_composite_reader_collects_messages_from_all_writers():
    """Three concurrent writers should all have their materializations observed.

    Each writer targets a distinct asset key so the asset framework does not see duplicate
    outputs for a single asset.
    """

    @dg.multi_asset(specs=[dg.AssetSpec("w0"), dg.AssetSpec("w1"), dg.AssetSpec("w2")])
    def multi(context: dg.AssetExecutionContext):
        reader = PipesCompositeMessageReader([PipesTempFileMessageReader() for _ in range(3)])
        with open_pipes_session(
            context=context,
            context_injector=PipesTempFileContextInjector(),
            message_reader=reader,
        ) as sess:
            # Composite params are exposed via PIPES_COMPOSITE_WRITERS_KEY and the per-writer helpers
            # unpack them into one env var mapping per writer.
            assert PIPES_COMPOSITE_WRITERS_KEY in sess.message_reader_params
            per_writer = sess.get_per_writer_bootstrap_env_vars()
            assert len(per_writer) == 3

            # Each writer must see its own distinct messages env var (otherwise they would
            # collide on the same file).
            messages_params = {str(ev[DAGSTER_PIPES_MESSAGES_ENV_VAR]) for ev in per_writer}
            assert len(messages_params) == 3
            context_params = {str(ev[DAGSTER_PIPES_CONTEXT_ENV_VAR]) for ev in per_writer}
            assert len(context_params) == 1  # context is shared across writers

            # Drive each simulated writer sequentially. True concurrency would require
            # isolating `PipesContext._instance` per thread — out of scope for this unit
            # test, which is asserting that the composite handler correctly aggregates from N
            # independent writer destinations.
            for i, ev in enumerate(per_writer):
                _simulate_external_process(dict(ev), f"w{i}", f"w{i}")

            # Give the reader threads a moment to drain their files.
            deadline = time.time() + 10
            while time.time() < deadline and sess.message_handler._closed_count < 3:  # noqa: SLF001
                time.sleep(0.1)

            assert sess.message_handler._opened_count == 3  # noqa: SLF001
            assert sess.message_handler._closed_count == 3  # noqa: SLF001
            assert sess.message_handler.received_opened_message is True
            assert sess.message_handler.received_closed_message is True

            yield from sess.get_results()

    with dg.DagsterInstance.ephemeral() as inst:
        result = dg.materialize([multi], instance=inst)

    assert result.success
    # Each writer reports exactly one materialization for its own asset key; verify all three
    # messages made it through the shared handler.
    all_mats = result.asset_materializations_for_node("multi")
    writer_labels = {str(m.metadata["writer"].value) for m in all_mats}
    assert writer_labels == {"w0", "w1", "w2"}


def test_composite_reader_requires_at_least_one_child():
    try:
        PipesCompositeMessageReader([])
    except dg.DagsterInvariantViolationError as e:
        assert "at least one" in str(e)
    else:
        raise AssertionError("expected DagsterInvariantViolationError for empty readers list")


def test_composite_reader_rejects_nested_multi_writer():
    # A composite reader with >1 child has expected_writer_count>1 and cannot itself be nested inside
    # another composite reader — chunk namespacing only works one level deep.
    inner = PipesCompositeMessageReader(
        [PipesTempFileMessageReader(), PipesTempFileMessageReader()]
    )
    try:
        PipesCompositeMessageReader([inner])
    except dg.DagsterInvariantViolationError as e:
        assert "single-writer" in str(e)
    else:
        raise AssertionError("expected DagsterInvariantViolationError for nested composite reader")


def test_single_writer_session_unchanged():
    """Single-writer sessions should behave identically to pre-composite behavior."""

    @dg.asset
    def single(context: dg.AssetExecutionContext):
        with open_pipes_session(
            context=context,
            context_injector=PipesTempFileContextInjector(),
            message_reader=PipesTempFileMessageReader(),
        ) as sess:
            # No composite key, single-element per-writer list
            assert PIPES_COMPOSITE_WRITERS_KEY not in sess.message_reader_params
            per_writer = sess.get_per_writer_bootstrap_env_vars()
            assert len(per_writer) == 1
            # Per-writer result matches legacy get_bootstrap_env_vars
            assert dict(per_writer[0]) == dict(sess.get_bootstrap_env_vars())

            _simulate_external_process(dict(per_writer[0]), "single", "w0")

            deadline = time.time() + 5
            while time.time() < deadline and sess.message_handler._closed_count < 1:  # noqa: SLF001
                time.sleep(0.05)

            assert sess.message_handler._opened_count == 1  # noqa: SLF001
            assert sess.message_handler._closed_count == 1  # noqa: SLF001

            yield from sess.get_results()

    with dg.DagsterInstance.ephemeral() as inst:
        result = dg.materialize([single], instance=inst)

    assert result.success


# ########################
# ##### HELPERS
# ########################


def _simulate_external_process(env: dict[str, str], asset_key: str, writer_label: str) -> None:
    """Run an external-style pipes block with the given bootstrap env vars.

    Each thread needs an isolated params loader (we cannot mutate `os.environ` concurrently)
    and a fresh `PipesContext` singleton. The singleton reset is a test-only concession; in
    real deployments each writer lives in its own process.
    """
    PipesContext._instance = None  # noqa: SLF001
    with open_dagster_pipes(params_loader=PipesMappingParamsLoader(env)) as ctx:
        ctx.report_asset_materialization(metadata={"writer": writer_label}, asset_key=asset_key)
    PipesContext._instance = None  # noqa: SLF001
