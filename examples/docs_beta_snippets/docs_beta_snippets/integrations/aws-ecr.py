from dagster_aws.ecr import ECRPublicResource

import dagster as dg


@dg.asset
def get_ecr_login_password(ecr_public: ECRPublicResource):
    return ecr_public.get_client().get_login_password()


defs = dg.Definitions(
    assets=[get_ecr_login_password],
    resources={"ecr_public": ECRPublicResource()},
)
