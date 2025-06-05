import dagster as dg
from dagster_evidence import EvidenceResource


@dg.asset(
    deps=["orders", "customers"]
)
def evidence_application(evidence: EvidenceResource):
    evidence.build()
