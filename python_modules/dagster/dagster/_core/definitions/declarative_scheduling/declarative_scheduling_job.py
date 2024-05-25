from typing import Iterable, Optional, Union

from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    SchedulingCondition,
)

"""
In declarative scheduling, everything happens within the context of a job.

Given that declarative scheduling's goal is the replace schedules, sensors, and AMP for
asset-based execution, that means we are left with a single concept to control asset-based
execution: the job.

A job performs a few important functions:

* It is a boundary in the operational domain. When a user boots up Dagster and asks the question
"is my stuff running", they will go to a job-oriented UI, such as the runs timeline.

* Within the context of a single job, their are targets (e.g. assets, asset checks, etc) that
have attached scheduling conditions. Through a cooperative process, the scheduling conditions
combined to determine the behavior of the job.


Under the hood:

* The job's scheduling decisions are driven by a scheduling loop, executed within a sensor. 
This sensor is created programmatically on the user's behalf.
* The job applies a default scheduling condition to all of its targets (see comment below
on the term target)


A job is comprised of:

* A scheduling policy, build upfront once or cooperatively from all of its targets.
    * In this framework, the function behind a sensor or a schdule is a scheduling policy.
* A set of targets, which are the assets, asset checks, etc that the job is responsible for. 
    * In the declarative scheduling world a legacy op-based job is just another type of target.



Implications:

* We previous had the thesis that we could get rid of jobs, and making all of our scheduling
and operational UIs think in terms of assets _only_. We would abandon the runs timeline, and
instead only have asset- or asset-group-oriented operational UI. To remove all ambiguity: 
**This PR proposes to abandon that goal**. 
* Very deliberately, the argument ot the object is named targets, not assets. This will allow
checks to be scheduled in addition to asset, as well as future proofs the name against future
renames and additional features. We could also support the selection syntax if we wanted to.
* It is possible that we can consolidate *all* execution under this model, including legacy non
asset-based execution. If an op or op graph could be target of a declarative scheduling job.
The scheduling condition would be used to control whether or those ops are executed. 
* `define_asset_job` would be supplanted by this and deprecated.
* The `job` and `jobs` arguments to sensors and schedules would be in an awkward place, since
they would not accept these jobs. We could mitigate with very explicit error messages.

What about schedules and sensors:

* Question: Could sensors and schedules that target assets be transformed to declarative scheduling
* Sensors still exist, but are thought of as a lower level abstraction (think: actor).



Questions:

* Can an asset be a target of more than one job? 

"""
from typing_extensions import TypeAlias

ExecutionTarget: TypeAlias = Union[AssetsDefinition, AssetChecksDefinition]


class DeclarativeSchedulingJob:
    def __init__(
        self,
        *,
        name: str,
        targets: Iterable[ExecutionTarget],
        default_scheduling_condition: Optional[SchedulingCondition] = None,
    ) -> None:
        self.name = name
        self.targets = targets
        self.default_scheduling_condition = default_scheduling_condition

    # Possible factory methods

    @staticmethod
    def cron(
        name: str, targets: Iterable[ExecutionTarget], cron_schedule: str
    ) -> "DeclarativeSchedulingJob":
        # check to see if targets already have a scheduling condition defined
        return DeclarativeSchedulingJob(
            name=name,
            targets=targets,
            default_scheduling_condition=SchedulingCondition.on_cron(cron_schedule),
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
