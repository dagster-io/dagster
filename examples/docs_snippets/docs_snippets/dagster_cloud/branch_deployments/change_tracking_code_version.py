from dagster import asset


# start_main_deployment
@asset(code_version="v1")
def customers():
    ...


# end_main_deployment


# start_branch_deployment
@asset(code_version="v2")
def customers():
    ...


# end_branch_deployment
