from unittest.mock import patch

from pandas import DataFrame

from docs_snippets.guides.dagster.enriching_with_software_defined_assets.vanilla_nothing import (
    users_recommender_job,
)


def test_users_recommender_job():
    with patch(
        "docs_snippets.guides.dagster.enriching_with_software_defined_assets.vanilla_nothing.read_sql"
    ) as mock_read_sql:
        mock_read_sql.return_value = DataFrame([{"COL1": "a", "COL2": 1}])

        assert users_recommender_job.execute_in_process().success
