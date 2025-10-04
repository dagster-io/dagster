"""Unit tests for compute log GraphQL schema utilities."""

from dagster._core.storage.compute_log_manager import CapturedLogData
from dagster_graphql.schema.logs.compute_logs import from_captured_log_data


def test_from_captured_log_data_with_valid_utf8():
    """Test that valid UTF-8 is decoded correctly."""
    log_data = CapturedLogData(
        log_key=["test", "key"],
        stdout=b"Hello stdout\n",
        stderr=b"Hello stderr\n",
        cursor="0",
    )

    result = from_captured_log_data(log_data)

    assert result.stdout == "Hello stdout\n"
    assert result.stderr == "Hello stderr\n"
    assert result.cursor == "0"
    assert result.logKey == ["test", "key"]


def test_from_captured_log_data_with_invalid_utf8_in_stderr():
    """Test that invalid UTF-8 bytes in stderr are replaced gracefully.

    This test verifies the fix for issue #32251 where invalid UTF-8 bytes
    would cause GraphQL query failures.
    """
    log_data = CapturedLogData(
        log_key=["test", "key"],
        stdout=b"Valid stdout\n",
        stderr=b"Valid before\n\xff\xfe\nValid after\n",  # Invalid UTF-8 sequence
        cursor="0",
    )

    result = from_captured_log_data(log_data)

    assert result.stdout == "Valid stdout\n"
    assert result.stderr is not None
    assert "Valid before" in result.stderr
    assert "Valid after" in result.stderr
    # Invalid bytes should be replaced with replacement character
    assert "\ufffd" in result.stderr


def test_from_captured_log_data_with_invalid_utf8_in_stdout():
    """Test that invalid UTF-8 bytes in stdout are replaced gracefully."""
    log_data = CapturedLogData(
        log_key=["test", "key"],
        stdout=b"Valid text\n\xf0\x9f\nMore text\n",  # Partial multi-byte UTF-8
        stderr=b"Valid stderr\n",
        cursor="0",
    )

    result = from_captured_log_data(log_data)

    assert result.stdout is not None
    assert "Valid text" in result.stdout
    assert "More text" in result.stdout
    # Partial multi-byte sequence should be replaced
    assert "\ufffd" in result.stdout
    assert result.stderr == "Valid stderr\n"


def test_from_captured_log_data_with_none_logs():
    """Test that None values for stdout/stderr are handled correctly."""
    log_data = CapturedLogData(
        log_key=["test", "key"],
        stdout=None,
        stderr=None,
        cursor="0",
    )

    result = from_captured_log_data(log_data)

    assert result.stdout is None
    assert result.stderr is None
    assert result.cursor == "0"
    assert result.logKey == ["test", "key"]


def test_from_captured_log_data_with_binary_data():
    """Test that completely binary (non-text) data is handled."""
    log_data = CapturedLogData(
        log_key=["test", "key"],
        stdout=b"\x00\x01\x02\x03\x04",  # Pure binary
        stderr=b"Text with\x00null bytes",
        cursor="0",
    )

    result = from_captured_log_data(log_data)

    # Should not raise an exception
    assert result.stdout is not None
    assert result.stderr is not None
    # Binary data should be replaced with replacement characters
    assert "\ufffd" in result.stdout or "\x00" in result.stdout
