"""Partner attribution for Snowflake consumption driven by Dagster.

Snowflake attributes consumption to a partner application by the connection's application name.
The Snowflake Python connector falls back to ``SF_PARTNER`` when a connection sets no name of its
own, which is what covers user code building its own Snowflake connections.
"""

import os

SNOWFLAKE_PARTNER_ENV_VAR = "SF_PARTNER"
SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER = "DagsterLabs_Dagster"


def set_snowflake_partner_env_var() -> None:
    """Advertise Dagster as the Snowflake partner application for this process.

    Leaves an existing value alone so a user's own attribution wins. Subprocesses launched by user
    code inherit the value.
    """
    os.environ.setdefault(SNOWFLAKE_PARTNER_ENV_VAR, SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER)
