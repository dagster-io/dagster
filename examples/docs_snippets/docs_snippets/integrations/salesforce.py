from pathlib import Path

from dagster_salesforce import SalesforceResource
from dagster_salesforce.credentials import SalesforceUserPasswordCredentials

import dagster as dg


@dg.asset(compute_kind="salesforce")
def salesforce_accounts(
    context: dg.AssetExecutionContext, salesforce: SalesforceResource
):
    """Query and export Account records from Salesforce."""
    # Get the Account object client
    account_obj = salesforce.get_object_client("Account")

    # Query accounts and save to CSV
    output_dir = Path("/tmp/salesforce_accounts")
    results = account_obj.query_to_csv(
        query="SELECT Id, Name, Type, Industry FROM Account LIMIT 1000",
        output_directory=output_dir,
        batch_size=10000,
    )

    context.log.info(f"Downloaded {sum(r.number_of_records for r in results)} accounts")

    # Create a new lead
    lead_obj = salesforce.get_object_client("Lead")
    lead_id = lead_obj.create_record(
        {
            "FirstName": "John",
            "LastName": "Doe",
            "Company": "Acme Corp",
            "Email": "john.doe@acmecorp.com",
        }
    )

    context.log.info(f"Created new lead with ID: {lead_id}")

    return {
        "accounts_exported": sum(r.number_of_records for r in results),
        "new_lead_id": lead_id,
    }


defs = dg.Definitions(
    assets=[salesforce_accounts],
    resources={
        "salesforce": SalesforceResource(
            credentials=SalesforceUserPasswordCredentials(
                username=dg.EnvVar("SALESFORCE_USERNAME"),
                password=dg.EnvVar("SALESFORCE_PASSWORD"),
                security_token=dg.EnvVar("SALESFORCE_SECURITY_TOKEN"),
                domain="login",  # or "test" for sandbox
            )
        ),
    },
)
