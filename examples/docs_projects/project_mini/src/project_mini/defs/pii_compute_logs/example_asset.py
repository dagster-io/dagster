import dagster as dg


@dg.asset
def process_customer_data() -> dg.MaterializeResult:
    # This log output contains PII that will be redacted
    print("Processing data for customer: John Doe")  # noqa: T201
    print("Email: john.doe@example.com")  # noqa: T201
    print("Phone: 555-123-4567")  # noqa: T201
    print("SSN: 123-45-6789")  # noqa: T201
    print("Credit Card: 4111-1111-1111-1111")  # noqa: T201
    print("IP Address: 192.168.1.100")  # noqa: T201

    return dg.MaterializeResult(metadata={"status": "processed"})
