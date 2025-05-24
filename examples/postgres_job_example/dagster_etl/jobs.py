from dagster import job, op
from .resources import postgres_resource
from ..sql import *


@op(required_resource_keys={'postgres'})
def update_customer_purchase(context):
    """Update the customer purchase table"""
    context.resources.postgres.execute_query(CUSTOMER_PURCHASE_INSERT_QUERY)


@job(resource_defs={'postgres': postgres_resource})
def update_tables():
    """Job for update all tables"""
    update_customer_purchase()
