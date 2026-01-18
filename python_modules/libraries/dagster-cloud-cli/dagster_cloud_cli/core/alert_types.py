from enum import Enum

from dagster_shared.serdes import whitelist_for_serdes


@whitelist_for_serdes
class InsightsAlertComparisonOperator(Enum):
    """Possible comparison operators for an insights alert type, used to
    determine when to trigger an alert based on the value of the metric.
    """

    LESS_THAN = "LESS_THAN"
    GREATER_THAN = "GREATER_THAN"

    def compare(self, computed_value: float, target_value: float) -> bool:
        if self == InsightsAlertComparisonOperator.LESS_THAN:
            return computed_value < target_value
        return computed_value > target_value

    def as_text(self) -> str:
        """Used in alert text to describe the comparison operator,
        e.g. usage is less than the limit or usage is greater than the limit.
        """
        if self == InsightsAlertComparisonOperator.LESS_THAN:
            return "less than"
        return "greater than"
