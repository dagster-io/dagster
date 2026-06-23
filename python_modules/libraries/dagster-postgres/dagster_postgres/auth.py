import abc
import logging
import threading
import time
from typing import Any

import sqlalchemy
from sqlalchemy import event

logger = logging.getLogger(__name__)


class PgTokenProvider(abc.ABC):
    """Abstract base for providers that supply short-lived database access tokens.

    Subclasses implement ``_fetch_token`` to obtain a fresh token from their
    respective cloud provider.  Caching and thread-safety are handled by the
    base class so that callers can simply invoke ``get_token()``.
    """

    def __init__(self) -> None:
        self._cached_token: str | None = None
        self._token_expiry: float = 0.0  # epoch seconds
        self._lock = threading.Lock()

    @abc.abstractmethod
    def _fetch_token(self) -> tuple[str, float]:
        """Return ``(token, expiry_epoch_seconds)``.

        If the exact expiry is unknown, implementations should return
        ``time.time() + 3600`` as a conservative default (1 hour).
        """
        ...

    def get_token(self) -> str:
        """Return a valid token, refreshing if expired or about to expire."""
        # Refresh 5 minutes before expiry to avoid races
        with self._lock:
            if self._cached_token is None or time.time() >= (self._token_expiry - 300):
                logger.debug("Refreshing PostgreSQL auth token")
                self._cached_token, self._token_expiry = self._fetch_token()
            return self._cached_token


class AzureWifTokenProvider(PgTokenProvider):
    """Azure Workload Identity Federation token provider.

    Uses ``DefaultAzureCredential`` which automatically picks up the
    ``AZURE_CLIENT_ID``, ``AZURE_TENANT_ID``, and
    ``AZURE_FEDERATED_TOKEN_FILE`` environment variables set by the Azure
    Workload Identity webhook on AKS pods.
    """

    def __init__(
        self,
        scope: str = "https://ossrdbms-aad.database.windows.net/.default",
    ) -> None:
        super().__init__()
        self._scope = scope
        self._credential: Any = None

    def _fetch_token(self) -> tuple[str, float]:
        if self._credential is None:
            try:
                from azure.identity import DefaultAzureCredential
            except ImportError:
                raise ImportError(
                    "azure-identity is required for Azure WIF auth. "
                    "Install with: pip install dagster-postgres[azure]"
                )
            self._credential = DefaultAzureCredential()
        token = self._credential.get_token(self._scope)
        return token.token, token.expires_on


class GcpWifTokenProvider(PgTokenProvider):
    """GCP Workload Identity Federation token provider.

    Uses Application Default Credentials (ADC), which automatically picks up
    the projected service account token on GKE pods.
    """

    def __init__(self) -> None:
        super().__init__()
        self._credentials: Any = None
        self._request: Any = None

    def _fetch_token(self) -> tuple[str, float]:
        if self._credentials is None:
            try:
                import google.auth
                import google.auth.transport.requests
            except ImportError:
                raise ImportError(
                    "google-auth is required for GCP WIF auth. "
                    "Install with: pip install dagster-postgres[gcp]"
                )
            self._credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            self._request = google.auth.transport.requests.Request()
        self._credentials.refresh(self._request)
        expiry = (
            self._credentials.expiry.timestamp()
            if self._credentials.expiry
            else (time.time() + 3600)
        )
        return self._credentials.token, expiry


class AwsWifTokenProvider(PgTokenProvider):
    """AWS IAM / IRSA token provider for RDS.

    Uses ``boto3`` to generate an RDS auth token.  Requires the hostname,
    port, username, and AWS region from the connection config.
    """

    def __init__(
        self,
        hostname: str,
        port: int,
        username: str,
        region: str,
    ) -> None:
        super().__init__()
        self._hostname = hostname
        self._port = port
        self._username = username
        self._region = region
        self._client: Any = None

    def _fetch_token(self) -> tuple[str, float]:
        if self._client is None:
            try:
                import boto3
            except ImportError:
                raise ImportError(
                    "boto3 is required for AWS WIF auth. "
                    "Install with: pip install dagster-postgres[aws]"
                )
            self._client = boto3.client("rds", region_name=self._region)
        token = self._client.generate_db_auth_token(
            DBHostname=self._hostname,
            Port=self._port,
            DBUsername=self._username,
        )
        # RDS auth tokens are valid for 15 minutes
        return token, time.time() + 900


def create_token_provider(
    auth_config: dict[str, Any],
    db_config: dict[str, Any] | None = None,
) -> PgTokenProvider:
    """Create a token provider from the ``auth_provider`` config block."""
    if "azure_wif" in auth_config:
        azure_cfg = auth_config["azure_wif"]
        return AzureWifTokenProvider(
            scope=azure_cfg.get("scope", "https://ossrdbms-aad.database.windows.net/.default"),
        )
    elif "gcp_wif" in auth_config:
        return GcpWifTokenProvider()
    elif "aws_wif" in auth_config:
        aws_cfg = auth_config["aws_wif"]
        if db_config is None:
            raise ValueError(
                "AWS WIF requires postgres_db config (not postgres_url) to"
                " extract hostname/port/username"
            )
        return AwsWifTokenProvider(
            hostname=db_config["hostname"],
            port=db_config.get("port", 5432),
            username=db_config["username"],
            region=aws_cfg["region"],
        )
    else:
        raise ValueError(f"Unknown auth_provider config: {auth_config}")


def register_do_connect_hook(
    engine: sqlalchemy.engine.Engine,
    token_provider: PgTokenProvider,
) -> None:
    """Register a ``do_connect`` event listener that injects a fresh token as
    the password before each DBAPI connection.
    """

    @event.listens_for(engine, "do_connect")
    def _inject_token(
        dialect: Any,
        conn_rec: Any,
        cargs: list[Any],
        cparams: dict[str, Any],
    ) -> None:
        cparams["password"] = token_provider.get_token()
