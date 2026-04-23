"""Tests for the password_provider feature (issue #33427).

Bug: dagster-postgres bakes the password into the connection URL at startup.
When using short-lived credentials (Azure AD tokens, AWS IAM tokens), the
password expires after ~60 minutes, but new connections still use the stale
token from the URL. Long-running workloads (daemon, sensors, schedules)
silently fail with authentication errors.

Fix: A `password_provider` config option that hooks into SQLAlchemy's
`do_connect` event to dynamically inject a fresh password/token on every
new database connection.
"""

from unittest.mock import MagicMock, patch

import pytest
import sqlalchemy
from dagster import _check as check
from dagster._core.errors import DagsterInvariantViolationError
from dagster_postgres.utils import get_conn_string, setup_pg_password_provider_event


# ---------------------------------------------------------------------------
# Helpers: simulate a rotating token provider (like Azure AD / AWS IAM)
# ---------------------------------------------------------------------------

_call_count = 0


def rotating_token_provider():
    """Simulates a token provider that returns a different token each time,
    mimicking Azure AD access token refresh behavior."""
    global _call_count
    _call_count += 1
    return f"token_v{_call_count}"


def dummy_valid_provider():
    return "secret123"


NON_CALLABLE_VAR = "I am a string, not a function"


def failing_provider():
    """Simulates a provider that fails at runtime (e.g., network error fetching
    an Azure AD token)."""
    raise ConnectionError("Azure AD endpoint unreachable")


def bad_return_type_provider():
    """Simulates a provider that returns a non-string value."""
    return 12345


# ---------------------------------------------------------------------------
# Bug reproduction: prove the problem exists without the fix
# ---------------------------------------------------------------------------


class TestBugReproduction:
    """Reproduce issue #33427: static passwords become stale."""

    def test_static_password_stays_stale_across_connections(self):
        """BUG: Without password_provider, the password is baked into the
        connection URL and never refreshed. Simulates what happens when an
        Azure AD token expires after the initial connection."""
        initial_token = "azure_ad_token_that_will_expire"
        conn_url = get_conn_string(
            username="dagster",
            password=initial_token,
            hostname="pg-host",
            db_name="dagster_db",
        )

        engine = sqlalchemy.create_engine(conn_url, poolclass=sqlalchemy.pool.NullPool)

        # The password is permanently embedded in the URL -- there is no
        # mechanism to update it when the token expires.
        # Note: str(engine.url) masks the password, so we use render_as_string
        rendered_url = engine.url.render_as_string(hide_password=False)
        assert initial_token in rendered_url

        # Simulate multiple connection attempts over time.  Each one would
        # reuse the same stale token from the URL.
        for _ in range(3):
            # The URL never changes, so every new psycopg2.connect() call
            # would send the original (now-expired) token.
            current_url = engine.url.render_as_string(hide_password=False)
            assert initial_token in current_url

    def test_password_provider_injects_fresh_token_every_connection(self):
        """FIX: With password_provider, the do_connect hook calls the provider
        on every new connection, injecting a fresh token into cparams."""
        global _call_count
        _call_count = 0

        engine = sqlalchemy.create_engine(
            "postgresql://dagster:placeholder@pg-host:5432/dagster_db",
            poolclass=sqlalchemy.pool.NullPool,
        )
        setup_pg_password_provider_event(
            engine,
            "dagster_postgres_tests.test_password_provider.rotating_token_provider",
        )

        # Mock psycopg2.connect so we don't need a real Postgres server.
        # The do_connect event fires BEFORE psycopg2.connect is called,
        # modifying cparams["password"] with the fresh token.
        captured_passwords = []

        original_connect = sqlalchemy.pool._ConnectionRecord  # noqa

        with patch("psycopg2.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_conn.encoding = "utf-8"
            mock_conn.cursor.return_value.__enter__ = MagicMock()
            mock_conn.cursor.return_value.__exit__ = MagicMock()
            mock_connect.return_value = mock_conn

            # Capture the password kwarg passed to psycopg2.connect
            def capture_connect(*args, **kwargs):
                captured_passwords.append(kwargs.get("password"))
                return mock_conn

            mock_connect.side_effect = capture_connect

            # Simulate 3 connection cycles (like a long-running daemon)
            for _ in range(3):
                try:
                    with engine.connect() as conn:
                        pass
                except Exception:
                    # We expect various errors since we're mocking psycopg2
                    # The important thing is that psycopg2.connect was called
                    pass

        # The provider should have been called for each connection attempt.
        # Each call should produce a DIFFERENT token, proving rotation works.
        assert _call_count >= 3, (
            f"Expected provider to be called at least 3 times, got {_call_count}"
        )
        # Verify ascending token versions were injected
        for i, pwd in enumerate(captured_passwords):
            assert pwd == f"token_v{i + 1}", (
                f"Connection {i + 1} got password '{pwd}', expected 'token_v{i + 1}'"
            )


# ---------------------------------------------------------------------------
# Unit tests: setup_pg_password_provider_event validation
# ---------------------------------------------------------------------------


class TestPasswordProviderSetup:
    """Test validation and error handling in setup_pg_password_provider_event."""

    def test_valid_provider_hooks_into_engine(self):
        """A valid dotted-path provider should register the do_connect listener."""
        engine = sqlalchemy.create_engine("sqlite:///:memory:")
        setup_pg_password_provider_event(
            engine,
            "dagster_postgres_tests.test_password_provider.dummy_valid_provider",
        )

        # The hook should fire and inject "password" into cparams.
        # SQLite doesn't accept a "password" kwarg, so it raises TypeError.
        with pytest.raises(TypeError, match="password"):
            with engine.connect() as conn:
                pass

    def test_invalid_format_raises_invariant_error(self):
        """A provider string without dots should raise immediately."""
        engine = sqlalchemy.create_engine("sqlite:///:memory:")
        with pytest.raises(
            DagsterInvariantViolationError,
            match="password_provider must be a dot-separated string",
        ):
            setup_pg_password_provider_event(engine, "invalid_format_no_dots")

    def test_missing_module_raises_invariant_error(self):
        """An unimportable module should raise with a clear message."""
        engine = sqlalchemy.create_engine("sqlite:///:memory:")
        with pytest.raises(
            DagsterInvariantViolationError,
            match="Could not import module",
        ):
            setup_pg_password_provider_event(
                engine, "this_module_absolutely_does_not_exist.get_token"
            )

    def test_missing_attribute_raises_invariant_error(self):
        """A valid module with a missing attribute should raise clearly."""
        engine = sqlalchemy.create_engine("sqlite:///:memory:")
        with pytest.raises(
            DagsterInvariantViolationError, match="Could not find callable"
        ):
            setup_pg_password_provider_event(
                engine, "dagster.NON_EXISTENT_ATTRIBUTE_DOES_NOT_EXIST"
            )

    def test_non_callable_attribute_raises_check_error(self):
        """A valid module.attribute that is not callable should raise CheckError."""
        engine = sqlalchemy.create_engine("sqlite:///:memory:")
        with pytest.raises(check.CheckError, match="not callable"):
            setup_pg_password_provider_event(
                engine,
                "dagster_postgres_tests.test_password_provider.NON_CALLABLE_VAR",
            )

    def test_provider_runtime_error_raises_clear_message(self):
        """If the provider callable raises at connection time, the error should
        be wrapped in a DagsterInvariantViolationError with a clear message."""
        engine = sqlalchemy.create_engine(
            "postgresql://dagster:placeholder@pg-host:5432/dagster_db",
            poolclass=sqlalchemy.pool.NullPool,
        )
        setup_pg_password_provider_event(
            engine,
            "dagster_postgres_tests.test_password_provider.failing_provider",
        )

        with patch("psycopg2.connect") as mock_connect:
            mock_connect.return_value = MagicMock()
            with pytest.raises(
                DagsterInvariantViolationError,
                match="raised an error while fetching credentials",
            ):
                with engine.connect() as conn:
                    pass

    def test_provider_bad_return_type_raises_clear_message(self):
        """If the provider returns a non-string, the error should clearly say so."""
        engine = sqlalchemy.create_engine(
            "postgresql://dagster:placeholder@pg-host:5432/dagster_db",
            poolclass=sqlalchemy.pool.NullPool,
        )
        setup_pg_password_provider_event(
            engine,
            "dagster_postgres_tests.test_password_provider.bad_return_type_provider",
        )

        with patch("psycopg2.connect") as mock_connect:
            mock_connect.return_value = MagicMock()
            with pytest.raises(
                DagsterInvariantViolationError,
                match="must return a str",
            ):
                with engine.connect() as conn:
                    pass


# ---------------------------------------------------------------------------
# Unit tests: get_conn_string XOR validation
# ---------------------------------------------------------------------------


class TestGetConnStringValidation:
    """Test the XOR validation: exactly one of password or password_provider."""

    def test_password_only_builds_valid_uri(self):
        uri = get_conn_string(
            username="foo", password="bar", hostname="host", db_name="db"
        )
        assert uri == "postgresql://foo:bar@host:5432/db"

    def test_password_provider_only_builds_uri_with_empty_password(self):
        uri = get_conn_string(
            username="foo",
            password_provider="my_module.get_token",
            hostname="host",
            db_name="db",
        )
        # Password placeholder is empty since the real token is injected at connect time
        assert uri == "postgresql://foo:@host:5432/db"

    def test_neither_provided_raises(self):
        with pytest.raises(
            check.CheckError,
            match="exactly one of `password` or `password_provider`",
        ):
            get_conn_string(username="foo", hostname="host", db_name="db")

    def test_both_provided_raises(self):
        with pytest.raises(
            check.CheckError,
            match="exactly one of `password` or `password_provider`",
        ):
            get_conn_string(
                username="foo",
                password="bar",
                hostname="host",
                db_name="db",
                password_provider="my_module.get_token",
            )

    def test_special_characters_in_password_are_url_encoded(self):
        uri = get_conn_string(
            username="user", password="p@ss:w0rd", hostname="h", db_name="d"
        )
        # quote() encodes @ and : but not /
        assert "p%40ss%3Aw0rd" in uri
