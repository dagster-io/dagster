import logging

import requests
from dagster import get_dagster_logger, __version__

class AirbyteResource:
    """
    This class exposes methods on top of the Airbyte REST API.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: str = "8000",
        request_max_retries: int = 3,
        request_retry_delay: float = 0.25,
        log: logging.Logger = get_dagster_logger(),
    ):
        self._host = host
        self._port = port

        self._log = log

    @property
    def api_base_url(self) -> str:
        return f"{self._host}:{self._port}/api/v1/"
    
    def make_request(self, endpoint: str, data: Optional[str]):
        """
        Creates and sends a request to the desired Airbyte REST API endpoint.

        Args:
            endpoint (str): The Fivetran API endpoint to send this request to.
            data (Optional[str]): JSON-formatted data string to be included in the request.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request
        """

        headers = {
            "User-Agent": f"dagster-airbyte/{__version__}",
            "accept": "application/json",
        }

        num_retries = 0
        while True:
            try:
                response = requests.request(
                    method="POST",
                    url=self.api_base_url + endpoint
                    headers=headers,
                    data=data,
                )
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                self._log.error("Request to Airbyte API failed: %s", e)
                if num_retries == self._request_max_retries:
                    break
                num_retries += 1
                time.sleep(self._request_retry_delay)

        raise Failure("Exceeded max number of retries.")
