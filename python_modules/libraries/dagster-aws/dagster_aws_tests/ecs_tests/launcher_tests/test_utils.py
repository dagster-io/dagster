from dagster_aws.ecs.utils import sanitize_family


def test_sanitize_family():
    assert sanitize_family("abc") == "abc"
    assert sanitize_family("abc123") == "abc123"
    assert sanitize_family("abc-123") == "abc-123"
    assert sanitize_family("abc_123") == "abc_123"
    assert sanitize_family("abc 123") == "abc123"
    assert sanitize_family("abc~123") == "abc123"
