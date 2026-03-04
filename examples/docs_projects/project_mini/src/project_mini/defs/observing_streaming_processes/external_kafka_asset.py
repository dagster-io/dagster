import dagster as dg

streaming_insurance_claims = dg.AssetSpec(
    key="streaming_insurance_claims",
    description="External Kafka stream of insurance claims managed by infrastructure team",
    group_name="streaming",
    kinds={"kafka", "streaming"},
    metadata={
        "source": "External Kafka",
        "topic": "insurance-claims-v1",
        "broker": "kafka.internal.company.com:9092",
        "managed_by": "Infrastructure Team",
    },
)
