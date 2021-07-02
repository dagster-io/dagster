from typing import Dict

from requests import codes, exceptions, post


class TeamsClient:
    def __init__(
        self,
        hook_url: str,
        http_proxy: str = None,
        https_proxy: str = None,
        timeout: float = 60,
        verify: bool = None,
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

    def post_message(self, payload: Dict) -> bool:
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
