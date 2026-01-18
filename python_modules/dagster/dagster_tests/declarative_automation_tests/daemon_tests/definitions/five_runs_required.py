import dagster as dg


def get_defs() -> dg.Definitions:
    # create assets with 10 distinct partitions definitions
    assets = []
    for i in range(5):

        @dg.asset(
            key=f"a{i}",
            partitions_def=dg.StaticPartitionsDefinition([f"{i}"]),
            automation_condition=dg.AutomationCondition.missing(),
        )
        def _a() -> None: ...

        assets.append(_a)

    return dg.Definitions(assets=assets)


defs = get_defs()
