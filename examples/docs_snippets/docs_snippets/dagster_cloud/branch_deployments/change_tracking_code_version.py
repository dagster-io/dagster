from dagster import asset


def scope_main_deployment():
    # start_main_deployment
    @asset(code_version="v1")
    def customers(): ...

    # end_main_deployment


def scope_branch_deployment():
    # start_branch_deployment
    @asset(code_version="v2")
    def customers(): ...

    # end_branch_deployment
