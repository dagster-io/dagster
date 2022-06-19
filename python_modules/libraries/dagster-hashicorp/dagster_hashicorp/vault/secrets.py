from abc import ABC, abstractmethod
from os import PathLike
from typing import Optional, Union

import hvac

from dagster import _check as check

AVAILABLE_KV_VERSIONS: list[int] = [1, 2]


class AuthType(ABC):
    @abstractmethod
    def auth(self, client: hvac.Client, **kwargs) -> None:
        """
        Accept hvac.Client and tries to authenticate it
        """
        raise NotImplementedError()


class TokenAuth(AuthType):
    def __init__(
        self,
        token: Optional[str] = None,
        token_path: Optional[Union[str, PathLike]] = None,
    ):
        if not token and not token_path:
            raise Exception("This authentication requires 'token' or 'token_path'")

        check.opt_str_param(token, "token")
        check.opt_path_param(token_path, "token_path")

        self.token = token
        self.token_path = token_path

    def auth(self, client: hvac.Client, **kwargs) -> None:
        if self.token_path:
            with open(self.token_path, encoding="utf8") as f:
                client.token = f.read()
        else:
            client.token = self.token


class UserpassAuth(AuthType):
    def __init__(self, username: str, password: str):
        check.str_param(username, "username")
        check.str_param(password, "password")

        self.username = username
        self.password = password

    def auth(self, client: hvac.Client, **kwargs) -> None:
        client.auth.userpass.login(
            username=self.username,
            password=self.password,
            **kwargs,
        )


class ApproleAuth(AuthType):
    def __init__(self, role_id: str, secret_id: str):
        check.str_param(role_id, "role_id")
        check.str_param(secret_id, "secret_id")

        self.role_id = role_id
        self.secret_id = secret_id

    def auth(self, client: hvac.Client, **kwargs) -> None:
        client.auth.approle.login(
            role_id=self.role_id,
            secret_id=self.secret_id,
            **kwargs,
        )


class KubernetesAuth(AuthType):
    def __init__(
        self,
        role: str,
        jwt_path: Union[str, PathLike] = "/var/run/secrets/kubernetes.io/serviceaccount/token",
    ):
        check.str_param(role, "role")
        check.path_param(jwt_path, "jwt_path")

        self.role = role
        self.jwt_path = jwt_path

    def auth(self, client: hvac.Client, **kwargs) -> None:
        with open(self.jwt_path, encoding="utf8") as f:
            jwt = f.read()

        client.auth.kubernetes.login(role=self.role, jwt=jwt, **kwargs)


class Vault:
    """
    A simple wrapper on the Vault client. It routes auth types.
    HashiCorp hvac documentation: https://hvac.readthedocs.io/en/stable/

    Args:
        auth_type (AuthType): A instance of auth type.
        url (str): URL to Vault
        # mount_point (Optional[str]): The “path” the method/backend was mounted on authentication
        kv_engine_version (int): The version of the engine
        verify (int): Either a boolean to indicate whether TLS verification
        # should be performed when sending requests to Vault,
        # or a string pointing at the CA bundle to use for verification.
        # See http://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification.
    """

    def __init__(
        self,
        auth_type: AuthType,
        url: Optional[str] = None,
        mount_point: Optional[str] = None,
        kv_engine_version: int = 2,
        verify: Union[bool, str] = True,
        **kwargs,
    ):
        check.param_invariant(isinstance(auth_type, (AuthType,)), "auth_type", "Should be AuthType")
        check.str_param(url, "url")
        check.opt_str_param(mount_point, "mount_point")
        check.int_param(kv_engine_version, "kv_engine_version")
        check.param_invariant(isinstance(verify, (int, bool)), "verify")
        check.param_invariant(kv_engine_version in AVAILABLE_KV_VERSIONS, "kv_engine_version")

        self.auth_type = auth_type
        self.url = url
        self.mount_point = mount_point
        self.kv_engine_version = kv_engine_version
        self.verify = verify
        self.kwargs = kwargs

        self.client = None

    def get_client(self) -> hvac.Client:
        """
        The returned an authenticated instance of hvac.Client.
        """
        if self.client is None:
            client = hvac.Client(url=self.url, verify=self.verify, **self.kwargs)

            auth_option = {}
            if self.mount_point:
                auth_option["mount_point"] = self.mount_point

            self.auth_type.auth(client, **auth_option)

            if not client.is_authenticated():
                raise Exception("Vault is not authentication")

            self.client = client

        return self.client

    def get_secret(
        self,
        secret_path: str,
        secret_version: Optional[int] = None,
    ) -> Optional[dict]:
        """
        Get secret value from the KV engine. The returned a dict.

        Args:
            secret_path (str): The path of the secret. Format: <mount_point>/data/<path>
            secret_version (Optional[int]): The version of secret, default the latest version
        """
        check.str_param(secret_path, "secret_path")
        check.opt_int_param(secret_version, "secret_version")

        try:
            mount_point, path = secret_path.split("/data/", 1)
        except ValueError:
            raise ValueError(
                f"Invalid secret path: {secret_path}.  Expected: '<mount_point>/data/<path>'"
            )

        if self.kv_engine_version == 1:
            if secret_version:
                raise ValueError("Only KV engine V2 can used the secret version")
            response = self.get_client().secrets.kv.v1.read_secret(
                path=path, mount_point=mount_point
            )
        else:
            response = self.get_client().secrets.kv.v2.read_secret_version(
                path=path, mount_point=mount_point, version=secret_version
            )

        return response["data"] if self.kv_engine_version == 1 else response["data"]["data"]
