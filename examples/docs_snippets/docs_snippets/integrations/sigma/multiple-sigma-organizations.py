from dagster_sigma import SigmaBaseUrl, SigmaOrganization

from dagster import Definitions, EnvVar
from dagster._core.definitions.decorators.definitions_decorator import definitions
from dagster._core.definitions.definitions_loader import DefinitionsLoadContext

sales_team_organization = SigmaOrganization(
    base_url=SigmaBaseUrl.AWS_US,
    client_id=EnvVar("SALES_SIGMA_CLIENT_ID"),
    client_secret=EnvVar("SALES_SIGMA_CLIENT_SECRET"),
)

marketing_team_organization = SigmaOrganization(
    base_url=SigmaBaseUrl.AWS_US,
    client_id=EnvVar("MARKETING_SIGMA_CLIENT_ID"),
    client_secret=EnvVar("MARKETING_SIGMA_CLIENT_SECRET"),
)


@definitions
def defs(context: DefinitionsLoadContext) -> Definitions:
    # We use Definitions.merge to combine the definitions from both organizations
    # into a single set of definitions to load
    return Definitions.merge(
        sales_team_organization.build_defs(context),
        marketing_team_organization.build_defs(context),
    )
