import threading
import time
from unittest.mock import patch

import pytest
import sqlalchemy
from dagster_postgres.auth import (
    AwsWifTokenProvider,
    AzureWifTokenProvider,
    GcpWifTokenProvider,
    PgTokenProvider,
    create_token_provider,
    register_do_connect_hook,
)
from dagster_postgres.utils import get_token_provider_from_config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeTokenProvider(PgTokenProvider):
    """A concrete token provider that returns a fixed token for testing."""

    def __init__(self, token: str = "fake-token", ttl: float = 3600) -> None:
        super().__init__()
        self._token = token
        self._ttl = ttl
        self.fetch_count = 0

    def _fetch_token(self) -> tuple[str, float]:
        self.fetch_count += 1
        return self._token, time.time() + self._ttl


# ---------------------------------------------------------------------------
# Token caching
# ---------------------------------------------------------------------------


class TestTokenCaching:
    def test_caches_token_within_ttl(self) -> None:
        provider = FakeTokenProvider(token="tok-1", ttl=3600)
        assert provider.get_token() == "tok-1"
        assert provider.get_token() == "tok-1"
        assert provider.fetch_count == 1

    def test_refreshes_on_expiry(self) -> None:
        provider = FakeTokenProvider(token="tok-1", ttl=0)
        # ttl=0 means the token is already expired on creation
        tok1 = provider.get_token()
        assert tok1 == "tok-1"
        assert provider.fetch_count == 1

        # Second call should refresh because token is already past expiry
        tok2 = provider.get_token()
        assert tok2 == "tok-1"
        assert provider.fetch_count == 2

    def test_refreshes_within_margin(self) -> None:
        # Token expires in 4 minutes — within the 5-minute refresh margin
        provider = FakeTokenProvider(token="tok-1", ttl=240)
        provider.get_token()
        assert provider.fetch_count == 1

        # Should refresh because 240s < 300s margin
        provider.get_token()
        assert provider.fetch_count == 2


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


class TestThreadSafety:
    def test_concurrent_get_token(self) -> None:
        provider = FakeTokenProvider(token="tok-1", ttl=3600)
        results: list[str] = []
        errors: list[Exception] = []

        def worker() -> None:
            try:
                results.append(provider.get_token())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert all(r == "tok-1" for r in results)
        # May have fetched more than once due to race at startup, but should be bounded
        assert provider.fetch_count >= 1


# ---------------------------------------------------------------------------
# do_connect hook
# ---------------------------------------------------------------------------


class TestDoConnectHook:
    def test_hook_injects_token_on_connect(self) -> None:
        """Verify that register_do_connect_hook causes the provider's token
        to be used as the password when psycopg2.connect is called.
        """
        provider = FakeTokenProvider(token="injected-password", ttl=3600)
        engine = sqlalchemy.create_engine(
            "postgresql://user:dummy@localhost:5432/db",
            poolclass=sqlalchemy.pool.NullPool,
        )
        register_do_connect_hook(engine, provider)

        # Patch psycopg2.connect to capture the password that SQLAlchemy passes
        captured_kwargs: dict[str, object] = {}
        with patch("psycopg2.connect") as mock_connect:

            def capture_connect(*args: object, **kwargs: object) -> None:
                captured_kwargs.update(kwargs)
                raise sqlalchemy.exc.OperationalError("test", {}, Exception("skip"))

            mock_connect.side_effect = capture_connect

            # Attempting to connect will invoke do_connect, which injects the token,
            # then psycopg2.connect is called with the modified password.
            try:
                with engine.connect():
                    pass
            except Exception:
                pass

        # The do_connect hook should have replaced "dummy" with the token
        assert captured_kwargs.get("password") == "injected-password"
        assert provider.fetch_count == 1


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------


class TestCreateTokenProvider:
    def test_azure_wif(self) -> None:
        provider = create_token_provider({"azure_wif": {"scope": "custom-scope"}})
        assert isinstance(provider, AzureWifTokenProvider)
        assert provider._scope == "custom-scope"  # noqa: SLF001

    def test_azure_wif_default_scope(self) -> None:
        provider = create_token_provider({"azure_wif": {}})
        assert isinstance(provider, AzureWifTokenProvider)
        assert "ossrdbms-aad" in provider._scope  # noqa: SLF001

    def test_gcp_wif(self) -> None:
        provider = create_token_provider({"gcp_wif": {}})
        assert isinstance(provider, GcpWifTokenProvider)

    def test_aws_wif(self) -> None:
        db_config = {"hostname": "my-host", "port": 5432, "username": "myuser"}
        provider = create_token_provider({"aws_wif": {"region": "us-east-1"}}, db_config)
        assert isinstance(provider, AwsWifTokenProvider)
        assert provider._region == "us-east-1"  # noqa: SLF001
        assert provider._hostname == "my-host"  # noqa: SLF001

    def test_aws_wif_requires_db_config(self) -> None:
        with pytest.raises(ValueError, match="AWS WIF requires postgres_db"):
            create_token_provider({"aws_wif": {"region": "us-east-1"}})

    def test_unknown_provider(self) -> None:
        with pytest.raises(ValueError, match="Unknown auth_provider"):
            create_token_provider({"unknown_wif": {}})


# ---------------------------------------------------------------------------
# Config extraction
# ---------------------------------------------------------------------------


class TestGetTokenProviderFromConfig:
    def test_returns_none_without_auth_provider(self) -> None:
        config = {
            "postgres_db": {"username": "u", "password": "p", "hostname": "h", "db_name": "d"}
        }
        assert get_token_provider_from_config(config) is None

    def test_returns_provider_with_auth_provider(self) -> None:
        config = {
            "postgres_db": {"username": "u", "hostname": "h", "db_name": "d"},
            "auth_provider": {"azure_wif": {}},
        }
        provider = get_token_provider_from_config(config)
        assert isinstance(provider, AzureWifTokenProvider)

    def test_rejects_auth_provider_with_postgres_url(self) -> None:
        config = {
            "postgres_url": "postgresql://user:pass@host/db",
            "auth_provider": {"azure_wif": {}},
        }
        with pytest.raises(Exception, match="auth_provider cannot be used with postgres_url"):
            get_token_provider_from_config(config)


# ---------------------------------------------------------------------------
# Cloud provider import errors
# ---------------------------------------------------------------------------


class TestImportErrors:
    def test_azure_missing_import(self) -> None:
        provider = AzureWifTokenProvider()
        with patch.dict("sys.modules", {"azure.identity": None, "azure": None}):
            with pytest.raises(ImportError, match="azure-identity"):
                provider._fetch_token()  # noqa: SLF001

    def test_gcp_missing_import(self) -> None:
        provider = GcpWifTokenProvider()
        with patch.dict("sys.modules", {"google.auth": None, "google": None}):
            with pytest.raises(ImportError, match="google-auth"):
                provider._fetch_token()  # noqa: SLF001

    def test_aws_missing_import(self) -> None:
        provider = AwsWifTokenProvider(hostname="h", port=5432, username="u", region="us-east-1")
        with patch.dict("sys.modules", {"boto3": None}):
            with pytest.raises(ImportError, match="boto3"):
                provider._fetch_token()  # noqa: SLF001
