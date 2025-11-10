from collections.abc import Callable

import dagster as dg


@dg.template_var
def generate_compliance_tags() -> Callable[[str, bool], dict[str, str]]:
    """Returns a function that generates compliance tags with computed retention logic.

    This demonstrates how to push complex business logic into Python functions
    instead of embedding it in template syntax.
    """

    def _generate_compliance_tags(
        classification: str, has_pii: bool = False
    ) -> dict[str, str]:
        # Complex business logic with full Python tooling support
        retention_mapping = {
            "public": 30,
            "internal": 90,
            "confidential": 180,
            "restricted": 365,
        }

        base_retention = retention_mapping.get(classification, 90)
        # Increase retention if PII is present
        if has_pii:
            base_retention *= 2

        return {
            "data_classification": classification,
            "retention_days": str(base_retention),
            "pii_contains": str(has_pii).lower(),
        }

    return _generate_compliance_tags
