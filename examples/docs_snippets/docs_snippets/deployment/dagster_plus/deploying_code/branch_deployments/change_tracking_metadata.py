from dagster import asset


def scope_main_deployment():
    # start_main_deployment
    @asset(metadata={"expected_columns": ["sku", "price", "supplier"]})
    def products(): ...

    # end_main_deployment


def scope_branch_deployment():
    # start_branch_deployment
    @asset(metadata={"expected_columns": ["sku", "price", "supplier", "backstock"]})
    def products(): ...

    # end_branch_deployment
