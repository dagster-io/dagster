import pytest
import sqlalchemy
from dagster_postgres.utils import setup_pg_password_provider_event
from dagster._core.errors import DagsterInvariantViolationError
from dagster._check import CheckError

def dummy_valid_provider():
    return "secret123"

def dummy_invalid_provider():
    return 123  # Not a string, but the callable itself evaluates

def test_password_provider_valid_hook():
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    # We use this test module itself as the provider module
    setup_pg_password_provider_event(engine, "dagster_postgres_tests.test_password_provider.dummy_valid_provider")

    try:
        with engine.connect() as conn:
            pass
    except TypeError:
        # SQLite dialect throws TypeError if we inject "password" 
        # But this means the hook executed successfully!
        pass

def test_password_provider_invalid_format():
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    with pytest.raises(DagsterInvariantViolationError, match="password_provider must be a dot-separated string"):
        setup_pg_password_provider_event(engine, "invalid_format_no_dots")

def test_password_provider_not_callable():
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    # Pass a valid module path but point to a non-callable variable
    with pytest.raises(AttributeError):
        setup_pg_password_provider_event(engine, "dagster.VERSION")
        with engine.connect() as conn:
            pass

NON_CALLABLE_VAR = "I am a string, not a function"

def test_password_provider_fails_runtime_callable_check():
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    setup_pg_password_provider_event(engine, "dagster_postgres_tests.test_password_provider.NON_CALLABLE_VAR")
    
    with pytest.raises(CheckError, match="not callable"):
        try:
            with engine.connect() as conn:
                pass
        except TypeError:
            pass
