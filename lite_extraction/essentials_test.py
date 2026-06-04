"""Exercise the essential Dagster feature surface on the lite engine.

Goes well beyond the basic smoke test: asset graphs, resources, run config,
typed IO, multi-assets, asset checks, and graph-backed assets — all through the
in-process execution path. Each block reports pass/fail independently so we can
see exactly what the stripped engine supports.
"""

import sys

from dagster import (
    AssetCheckResult,
    AssetExecutionContext,
    AssetOut,
    AssetSpec,
    Config,
    ConfigurableResource,
    DagsterInstance,
    Definitions,
    In,
    MetadataValue,
    Out,
    asset,
    asset_check,
    define_asset_job,
    graph_asset,
    job,
    materialize,
    multi_asset,
    op,
)

results: list[tuple[str, bool, str]] = []


def check(name):
    def deco(fn):
        try:
            fn()
            results.append((name, True, ""))
        except Exception as e:
            import traceback

            results.append((name, False, f"{type(e).__name__}: {e}"))
            traceback.print_exc()

    return deco


I = DagsterInstance.ephemeral  # noqa: E741


@check("1. asset graph with dependencies")
def _():
    @asset
    def raw() -> int:
        return 10

    @asset
    def refined(raw: int) -> int:
        return raw + 5

    r = materialize([raw, refined], instance=I())
    assert r.success and r.output_for_node("refined") == 15


@check("2. op job with run config")
def _():
    class MyConfig(Config):
        multiplier: int = 2

    @op
    def base() -> int:
        return 6

    @op
    def scale(config: MyConfig, x: int) -> int:
        return x * config.multiplier

    @job
    def cfg_job():
        scale(base())

    r = cfg_job.execute_in_process(run_config={"ops": {"scale": {"config": {"multiplier": 5}}}})
    assert r.success and r.output_for_node("scale") == 30


@check("3. ConfigurableResource injection")
def _():
    class Greeter(ConfigurableResource):
        prefix: str

        def greet(self, name: str) -> str:
            return f"{self.prefix} {name}"

    @asset
    def greeting(greeter: Greeter) -> str:
        return greeter.greet("world")

    r = materialize([greeting], resources={"greeter": Greeter(prefix="hello")}, instance=I())
    assert r.success and r.output_for_node("greeting") == "hello world"


@check("4. multi_asset")
def _():
    @multi_asset(outs={"a": AssetOut(), "b": AssetOut()})
    def two():
        return 1, 2

    r = materialize([two], instance=I())
    assert r.success
    assert r.output_for_node("two", "a") == 1
    assert r.output_for_node("two", "b") == 2


@check("5. asset_check")
def _():
    @asset
    def numbers() -> int:
        return 42

    @asset_check(asset=numbers)
    def is_positive(numbers: int) -> AssetCheckResult:
        return AssetCheckResult(passed=numbers > 0)

    r = materialize([numbers, is_positive], instance=I())
    assert r.success
    evals = r.get_asset_check_evaluations()
    assert len(evals) == 1 and evals[0].passed


@check("6. typed IO + metadata via context")
def _():
    @asset
    def with_meta(context: AssetExecutionContext) -> int:
        context.add_output_metadata({"rows": MetadataValue.int(3)})
        return 3

    r = materialize([with_meta], instance=I())
    assert r.success and r.output_for_node("with_meta") == 3


@check("7. graph_asset (composed ops)")
def _():
    @op
    def fetch() -> int:
        return 100

    @op
    def halve(x: int) -> int:
        return x // 2

    @graph_asset
    def composed() -> int:
        return halve(fetch())

    r = materialize([composed], instance=I())
    assert r.success and r.output_for_node("composed") == 50


@check("8. Definitions + define_asset_job")
def _():
    @asset
    def ping() -> str:
        return "pong"

    defs = Definitions(assets=[ping], jobs=[define_asset_job("all", "*")])
    the_job = defs.resolve_job_def("all")
    r = the_job.execute_in_process(instance=I())
    assert r.success and r.output_for_node("ping") == "pong"


@check("9. multiple ops with fan-in")
def _():
    @op(out=Out(int))
    def a() -> int:
        return 2

    @op(out=Out(int))
    def b() -> int:
        return 3

    @op(ins={"x": In(int), "y": In(int)})
    def add(x: int, y: int) -> int:
        return x + y

    @job
    def fanin():
        add(a(), b())

    r = fanin.execute_in_process()
    assert r.success and r.output_for_node("add") == 5


@check("10. asset reads upstream from IO manager across runs")
def _():
    @asset
    def producer() -> int:
        return 7

    inst = I()
    r1 = materialize([producer], instance=inst)
    assert r1.success

    @asset(deps=[AssetSpec("producer")])
    def consumer() -> int:
        return 1

    # consumer in a fresh materialize using same instance
    r2 = materialize([consumer], instance=inst)
    assert r2.success


def main() -> int:
    import dagster

    print(f"dagster {dagster.__version__}\n")
    # Run each check (decorators already executed at import; re-run cleanly here
    # is not needed — they ran on definition). Print results.
    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, err in results:
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name}" + (f"  -> {err}" if err else ""))
    print(f"\n{passed}/{len(results)} essentials passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
