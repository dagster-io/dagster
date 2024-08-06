# Description: This file contains the Snowflake connection identifiers for the Snowflake partner account.
# The connection identifiers are used to identify the partner account when connecting to Snowflake.

# We use different connection identifiers for different connection code paths to ensure that each is
# working as expected.
SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER = "DagsterLabs_Dagster"
SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER_SQLALCHEMY = "DagsterLabs_Dagster_SqlAlchemy"
