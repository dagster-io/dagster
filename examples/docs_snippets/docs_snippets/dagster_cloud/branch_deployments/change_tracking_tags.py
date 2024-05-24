from dagster import asset


def scope_main_deployment():
    # start_main_deployment
    @asset(tags={"section": "produce"})
    def fruits_in_stock(): ...

    # end_main_deployment


def scope_branch_deployment():
    # start_branch_deployment
    @asset(tags={"section": "produce", "type": "perishable"})
    def fruits_in_stock(): ...

    # end_branch_deployment
