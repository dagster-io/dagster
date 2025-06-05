from dagster_evidence import EvidenceResource

import dagster as dg


@dg.asset(deps=["orders", "customers"])
def evidence_application(evidence: EvidenceResource):
    evidence.build()
