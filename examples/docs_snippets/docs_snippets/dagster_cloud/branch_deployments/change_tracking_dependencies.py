from dagster import asset


@asset
def orders(): ...


@asset
def customers(): ...


def scope_main_deployment():
    # start_main_deployment
    @asset(deps=[orders])
    def returns(): ...

    # end_main_deployment


def scope_branch_deployment():
    # start_branch_deployment
    @asset(deps=[orders, customers])
    def returns(): ...

    # end_branch_deployment
