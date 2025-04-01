import os

import dagster as dg
from atproto import Client


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
