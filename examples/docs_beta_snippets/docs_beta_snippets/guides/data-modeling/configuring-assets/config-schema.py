import dagster as dg


class ForecastModelConfig(dg.Config):
    # lookback_window_days defaults to 30, but can be
    # overridden by the user. If you do not provide a
    # default, the user will need to provide a value.
    lookback_window_days: int = 30


@dg.asset
def forecast_model(config: ForecastModelConfig):
    print("Running with parallelism:", config.lookback_window_days)  # noqa: T201
    # ...more code here


defs = dg.Definitions(assets=[forecast_model])

if __name__ == "__main__":
    from pathlib import Path

    import yaml

    dg.materialize(
        [forecast_model],
        run_config=yaml.safe_load(
            (Path(__file__).absolute().parent / "run_config.yaml").open()
        ),
    )
