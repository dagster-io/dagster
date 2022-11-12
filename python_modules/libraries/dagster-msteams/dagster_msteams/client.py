from typing import Mapping, Optional

from requests import codes, exceptions, post


class TeamsClient:
    """MS Teams web client responsible for connecting to a channel using the webhook URL
    and posting informaton in the form of cards."""

    def __init__(
        self,
        hook_url: str,
        http_proxy: Optional[str] = None,
        https_proxy: Optional[str] = None,
        timeout: Optional[float] = 60,
        verify: Optional[bool] = None,
    ):
        self._hook_url = hook_url
        self._timeout = timeout
        self._verify = verify
        if http_proxy is None and https_proxy is None:
            self._proxy = None
        else:
            self._proxy = {}
            if http_proxy:
                self._proxy["http"] = http_proxy
            if https_proxy:
                self._proxy["https"] = https_proxy
        self._headers = {"Content-Type": "application/json"}

    def post_message(self, payload: Mapping) -> bool:  # pragma: no cover
        response = post(
            self._hook_url,
            json=payload,
            headers=self._headers,
            proxies=self._proxy,
            timeout=self._timeout,
            verify=self._verify,
        )
        if response.status_code == codes.ok and response.text == "1":  # pylint: disable=no-member
            return True
        else:
            raise exceptions.RequestException(response.text)
