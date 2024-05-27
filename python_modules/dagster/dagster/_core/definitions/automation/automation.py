from typing import Iterable, NamedTuple, Optional, Union

from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    SchedulingCondition,
)

"""
In declarative automation, everything happens within the context of an automation.

Given that declarative automation's goal is the replace schedules, sensors, and AMP for
asset-based execution, that means we are left with a single concept to control asset-based
execution: the automation.

An automation performs a few important functions:

* It is a boundary in the operational domain. When a user boots up Dagster and asks the question
"is my stuff running", they will go to an automation-oriented UI, such as the runs timeline. In the
runs timeline there is a row per automation.

* Within the context of a single automation, there are targets (e.g. assets, asset checks, etc) that
have attached automation conditions. Through a cooperative process, the automation conditions
combined to determine the behavior of the job.

Under the hood:

* The automation's scheduling decisions are driven by a scheduling loop, executed within a sensor. 
This sensor is created programmatically on the user's behalf.
* The job applies a default automation condition to all of its targets (see comment below
on the term target)

Implications:

* We previous had the thesis that we could get rid of formal groupings of assets operationally,
and making all of our scheduling and operational UIs think in terms of assets _only_.
We would abandon the runs timeline, and instead only have asset- or asset-group-oriented
operational UI. To remove all ambiguity: **This PR proposes to abandon that goal**. 
* Very deliberately, the argument to the object is named targets, not assets. This is for a few reasons:
    * This will allow checks to be scheduled in addition to assets
    * Future proofs the name against future renames and additional features. 
    * We could also support the selection syntax if we wanted to. 
    * It is possible that we can consolidate *all* execution under this model, including legacy 
      non-asset-based execution. If an op or op graph could be target of an automation.  

What about schedules and sensors:

Questions:

* Can an asset be a target of more than one job? 

"""
from typing_extensions import TypeAlias

ExecutionTarget: TypeAlias = Union[AssetsDefinition, AssetChecksDefinition]


class AutomationCondition(NamedTuple):
    scheduling_condition: SchedulingCondition


class Automation:
    def __init__(
        self,
        *,
        name: str,
        targets: Iterable[ExecutionTarget],
        default_automation_condition: Optional[AutomationCondition] = None,
    ) -> None:
        self.name = name
        self.targets = targets
        self.default_automation_condition = default_automation_condition

    # Possible factory methods

    @staticmethod
    def cron(name: str, targets: Iterable[ExecutionTarget], cron_schedule: str) -> "Automation":
        # check to see if targets already have a scheduling condition defined
        return Automation(
            name=name,
            targets=targets,
            default_automation_condition=AutomationCondition(
                SchedulingCondition.on_cron(cron_schedule)
            ),
        )

    # @staticmethod
    # def manual(name: str, targets: Iterable[ExecutionTarget]) -> "DeclarativeSchedulingJob":
    #     return DeclarativeSchedulingJob(
    #         name=name,
    #         targets=targets,
    #         default_scheduling_condition=None,  # TODO add placeholder to disallow policies?
    #     )

    # @staticmethod
    # def on_upstream_update(
    #     name: str, targets: Iterable[ExecutionTarget]
    # ) -> "DeclarativeSchedulingJob": ...

    # @staticmethod
    # # some replacement for arbitrary-sensor-like behavior
    # def on_event(name: str, targets: Iterable[ExecutionTarget]) -> "DeclarativeSchedulingJob": ...

    # @staticmethod
    # # Every asset is on demend within the job. Anytime any other asset is scheduled, everything
    # # upstream and downstream is included in the launch
    # def on_demand(name: str, targets: Iterable[ExecutionTarget]) -> "DeclarativeSchedulingJob": ...

    # @staticmethod
    # def cooperative(
    #     name: str, targets: Iterable[ExecutionTarget]
    # ) -> "DeclarativeSchedulingJob": ...
