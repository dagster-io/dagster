from project_mini.defs.pii_compute_logs.pii_redactor import redact_pii


def test_redacts_email():
    result = redact_pii("Contact us at user@example.com for support.")
    assert "user@example.com" not in result
    assert "[EMAIL]" in result


def test_redacts_phone():
    result = redact_pii("Call 555-867-5309 to speak with an agent.")
    assert "555-867-5309" not in result
    assert "[PHONE]" in result


def test_redacts_ssn():
    result = redact_pii("Employee SSN: 123-45-6789")
    assert "123-45-6789" not in result
    assert "[SSN]" in result


def test_redacts_credit_card():
    result = redact_pii("Card number: 1234 5678 9012 3456")
    assert "1234 5678 9012 3456" not in result
    assert "[CREDIT_CARD]" in result


def test_redacts_ip_address():
    result = redact_pii("Request from IP 192.168.1.100")
    assert "192.168.1.100" not in result
    assert "[IP_ADDRESS]" in result


def test_clean_text_unchanged():
    text = "This log line contains no sensitive data at all."
    assert redact_pii(text) == text


def test_redacts_multiple_pii_in_one_string():
    text = "User john@acme.com called from 800-555-1234"
    result = redact_pii(text)
    assert "[EMAIL]" in result
    assert "[PHONE]" in result
    assert "john@acme.com" not in result
    assert "800-555-1234" not in result
