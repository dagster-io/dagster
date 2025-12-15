from datetime import datetime
from typing import Any

import dagster as dg
import requests


class APIClientResource(dg.ConfigurableResource):
    """Resource for connecting to an HTTP API to pull data.

    This resource makes real HTTP requests to an API endpoint.
    For testing, override this resource with a mock implementation.
    """

    base_url: str = "http://localhost:5051"
    timeout_seconds: int = 30

    def get_records(self, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
        """Fetch records from the API within the given date range.

        Args:
            start_date: Start of the date range (inclusive)
            end_date: End of the date range (exclusive)

        Returns:
            List of records from the API
        """
        response = requests.get(
            f"{self.base_url}/records",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
