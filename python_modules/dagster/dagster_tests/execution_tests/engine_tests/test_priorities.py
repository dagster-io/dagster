import dagster as dg


@dg.op(tags={"dagster/priority": "-1"})
def low(_):
    pass


@dg.op
def none(_):
    pass


@dg.op(tags={"dagster/priority": "1"})
def high(_):
    pass


@dg.job
def priority_test():
    none()
    low()
    high()
    none()
    low()
    high()


def test_priorities():
    result = priority_test.execute_in_process()
    assert result.success
    assert [str(event.node_handle) for event in result.get_step_success_events()] == [
        "high",
        "high_2",
        "none",
        "none_2",
        "low",
        "low_2",
    ]


def test_priorities_mp():
    with dg.instance_for_test() as instance:
        recon_job = dg.reconstructable(priority_test)
        with dg.execute_job(
            recon_job,
            run_config={
                "execution": {"config": {"multiprocess": {"max_concurrent": 1}}},
            },
            instance=instance,
        ) as result:
            assert result.success
            assert [str(event.node_handle) for event in result.get_step_success_events()] == [
                "high",
                "high_2",
                "none",
                "none_2",
                "low",
                "low_2",
            ]
