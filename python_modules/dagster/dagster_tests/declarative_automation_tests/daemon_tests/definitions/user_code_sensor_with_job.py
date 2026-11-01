import dagster as dg

# The SUPPORTED user-code combination: a use_user_code_server=True sensor targeting an
# eager asset, coexisting with a conditioned job that is unclaimed and therefore lands
# on the default (daemon-evaluated) automation condition sensor. Job keys on the
# user-code sensor itself are guarded off at definition time.
#
#     external (manual)
#        +--> a            eager(), targeted by user_code_sensor
#        +--> b            member of my_job: all_job_root_assets_match(eager())


@dg.asset
def external() -> None: ...


@dg.asset(deps=[external], automation_condition=dg.AutomationCondition.eager())
def a() -> None: ...


@dg.asset(deps=[external])
def b() -> None: ...


my_job = dg.define_asset_job(
    "my_job",
    selection=[b],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.eager()
    ),
)

defs = dg.Definitions(
    assets=[external, a, b],
    jobs=[my_job],
    sensors=[
        dg.AutomationConditionSensorDefinition(
            "user_code_sensor",
            target=[a],
            use_user_code_server=True,
        )
    ],
)
