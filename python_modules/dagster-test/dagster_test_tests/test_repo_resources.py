from dagster_test.toys.repo_resources.repos import dev_repo, prod_repo


def test_dev_repo():
    dev_repo.get_pipeline("bar").execute_in_process()
    dev_repo.get_pipeline("other_bar").execute_in_process(
        run_config={"ops": {"other_foo": {"config": {"efg": "value"}}}}
    )


def test_prod_repo():
    prod_repo.get_pipeline("bar").execute_in_process()
    prod_repo.get_pipeline("other_bar").execute_in_process(
        run_config={"ops": {"other_foo": {"config": {"efg": "value"}}}}
    )
