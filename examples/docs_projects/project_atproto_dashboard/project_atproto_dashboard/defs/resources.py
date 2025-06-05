import os

import dagster as dg
from atproto import Client
from dagster_aws.s3 import S3Resource
from dagster_dbt import DbtCliResource
from project_atproto_dashboard.defs.assets.modeling import dbt_project


# start_resource
class ATProtoResource(dg.ConfigurableResource):
    login: str
    password: str
    session_cache_path: str = "atproto-session.txt"

    def _login(self, client):
        """Create a re-usable session to be used across resource instances; we are rate limited to 30/5 minutes or 300/day session."""
        if os.path.exists(self.session_cache_path):
            with open(self.session_cache_path) as f:
                session_string = f.read()
            client.login(session_string=session_string)
        else:
            client.login(login=self.login, password=self.password)
            session_string = client.export_session_string()
            with open(self.session_cache_path, "w") as f:
                f.write(session_string)

    def get_client(
        self,
    ) -> Client:
        client = Client()
        self._login(client)
        return client


# end_resource


dbt_resource = DbtCliResource(project_dir=dbt_project)


atproto_resource = ATProtoResource(
    login=dg.EnvVar("BSKY_LOGIN"), password=dg.EnvVar("BSKY_APP_PASSWORD")
)

s3_resource = S3Resource(
    endpoint_url=dg.EnvVar("AWS_ENDPOINT_URL"),
    aws_access_key_id=dg.EnvVar("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=dg.EnvVar("AWS_SECRET_ACCESS_KEY"),
    region_name="auto",
)
