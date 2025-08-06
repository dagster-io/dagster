from dagster._core.instance.scheduling.scheduling_domain import SchedulingDomain

__all__ = ["SchedulingDomain"]

# For backward compatibility, provide scheduling_implementation as SchedulingDomain
scheduling_implementation = SchedulingDomain
