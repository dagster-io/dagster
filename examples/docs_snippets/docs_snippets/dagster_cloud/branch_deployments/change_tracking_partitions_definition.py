from dagster import WeeklyPartitionsDefinition, asset


def scope_main_deployment():
    # start_main_deployment
    @asset(partitions_def=WeeklyPartitionsDefinition(start_date="2024-01-01"))
    def weekly_orders(): ...

    # end_main_deployment


def scope_branch_deployment():
    # start_branch_deployment
    @asset(partitions_def=WeeklyPartitionsDefinition(start_date="2023-01-01"))
    def weekly_orders(): ...

    # end_branch_deployment
