from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple, Optional

from dagster import _check as check
from dagster._core.definitions.data_version import CachingStaleStatusResolver
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partition import PartitionsDefinition

if TYPE_CHECKING:
    from dagster._core.definitions.internal_asset_graph import InternalAssetGraph
    from dagster._core.definitions.repository_definition.repository_definition import (
        RepositoryDefinition,
    )
    from dagster._core.instance import DagsterInstance
    from dagster._core.reactive_scheduling.asset_graph_view import (
        AssetGraphView,
        AssetSlice,
        AssetSliceFactory,
    )
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

    from .expr import ExprNode
    from .scheduling_sensor import SensorSpec


class ScheduleLaunchResult(NamedTuple):
    launch: bool = True
    explicit_launching_slice: Optional["AssetSlice"] = None
    cursor: Optional[str] = None


class EvaluationResult(NamedTuple):
    asset_slice: "AssetSlice"


"""
AMP vNext: Reactive Scheduling

Goals:
* Replaces schedules, sensors, and AMP for asset-based execution. 
  Built on sensors, but that is an implementation detail. Sensors 
  and schedules should only be directly used for advanced use cases.
* Improved observability
* Reduced blast radius and better operational safety 
* Better pluggability and customizability
* Rationalized programming model so that it is simpler and easier to 
  write scheduling rules.

Concrete differences with AMP:
* Launches backfills, not runs: The current AMP has, in effect, a "shadow" backfilling
  system that refreshes historical partitions, issuing many runs along the way. This makes
  that system difficult-to-operate (e.g. you have to cancel runs individually) and dangerous. 
  Instead reactive scheduling stacks on top of the backfilling capability to manage 
  long-running operations that issue many runs to get large sets of asset partitions
  up-to-date. This will consolidate code paths and also place pressure on ourselves to 
  improve asset backfilling and make it "first-class", which is a good outcome.

  We will also be able to stack on other backfill features, such as the abiliy to preview a backfill
  plan. One can easily imagine a reactive scheduling tool that simulates a tick and shows you the
  backfill or backfills that *would* have been issued.

  A natural extension of this work is to consolidate all asset-based execution onto the
  backfill system and to mature the backfill system as a result.

* Simplified programming model: The current AMP internal has a complex programming model
  that is difficult to understand and model. Exposing this API to users would not be succesful, and
  it is too hard for our own engineers to understand quickly.

* Optimizes for incremental computation, not historical backfills: Reactive scheduling (RS) focuses
  on incremental computation as time progresses, not attempting to backfill arbitrarily far
  in the past. This limits how much computation we have to do, and reduces operational blast radius.

* Executes in the user cloud with pluggability for user-defined behavior: With the above
  constraint, it is now more plausible to execute this completely in the user cloud, which
  in turn makes a user pluggability story more straightforward.

* Each asset has a *launch* function and an *evaluation* function: RS continually ticks, evaluating
  all asset partitions in a particular zone of control. Note: In the current state this in effect
  just a code location, but we will want more flexibility than that.

A scheduling policy has two subcomponents
1. An evaluation function
2. An optional launch function.

The mental model of this algorithm is that at any point in time, an asset's launcher
in the graph requests a launch, because the author of that asset believes
that a launch is required to fulfill an SLA. (It requests a set partitions within
that asset [referred to an asset slice in this doc]) The decision to launch is
business logic, and therefore a user-defined function.  There are out-of-box
policies for common use cases (e.g. a cron schedule, a parent asset has updated, etc). 
Underneath the hood, each a launch function is attached to a sensor that executes
that launch function.

This covers both lazy and eager scheduling.

 Examples
 * Eager launch policies, typically root of the zone:
   * Run ELT (e.g. Fivetran, Airbyte) every hour. This would be a launching
     policy at the root. The data needs to be moved eagerly because the
     loading needs to be incremental. So doing it this way is the only
     way for the zone of control to meet its SLA.
   * Launch whenever upstream asset partition is materialized, whether it is 
     in the zone of control or not. This is the "asset sensor" use case.
 * Lazy launch policies, typically within the zone:
   * Unconditially launch on a cron schedule. The user needs to know the general
     properties of the upstream zone in order for this to make sense as they need to
     understand how long operations can potentially take. With multiple crons
     in this structure this can solve the "Skip daily table in 23/24 runs" problem laid
     out in original blog post with single workflows with heterogenous time-grained
     partitioning schemes. Meaning one asset could be scheduled daily, and another
     hourly, and the system would ensure that we do not double materialize shared
     upstream assets.
   * Launch once a day at a specific time (e.g 1 a.m.) on a schedule, but only after
     specific source data upstream has hit *after* that time.
   * Launch based on the result of an API call.

It first walks up the tree to discover the candidates for launch at the root of zone of control.
This determines the candidate partition space. There are rules that limit the size of the candidate
space on any particular tick, to make computation tractable. The default behavior is that reactive
scheduling only considers the current time window. In other words, it schedules work incrementally,
looking forward in time.

Default Rules:
   * On launch, only the latest time partition is considered by default.
   * By default, when navigating from an unpartitioned asset to a partitioned asset
     only the latest partition is considered on the partitioned asset.
      * Note: we informally do this in parts of the code base today that compute "ancestors" and in the on_parent_updated
      rule in AMP. See asset_partitions_with_newly_updated_parents_and_new_cursor,
      and get_parent_asset_partitions_updated_after_child

For non-incremental work (e.g. historical backfills) the expectation is that this requires *manual*
operation. This is a conscious design decision. Large, historical backfills are too expensive
and too dangerous to be automatic.

Then the scheduler traverses the space to determine the set of asset partitions to include in the launch request.
This is the launch partition space.  Whether or not an asset partition is included is also business logic. It
does this by running the evaluation function at every asset node.

Examples:
   * Unconditionally include
   * Only include if the parents are included
   * Only include if unsynced
   * Only include at most once every 8 hours.
   + Only include weekdays, respecting the customer holiday schedule.
   * Only include if one parent is updated. We can tolerate outdated data from another parent.
   * Do not include if already targeted for materialization by another scheduled launch.
   * Only include if spot prices are below a certain threshold.
   * Respect a quota system that assigns costs to downstream teams and limits comptuation on a per-team basis.

For common rules, we provide an expression-based DSL that can do boolean logic on pre-defined rules.

The end goal is to set up a scheduling zone does the optimal, minimal set of calculations to
get the zone a state that fulfills its SLAs. This is a cooperative process, where individual
assets decide to instigate launches, and then constrain their inclusion in those launches
via the evaluation process, and does so in a distributed manner.

** Rationalizing our stack **:

With the additional of AMP, asset partitions, dynamic partitioning, and other related features, the complexity
of our system has outstripped the ability of our abstractions to model it. A shallow indication of this our repeated
threading of current time/evaluation time, storage_id/cursors, and dynamic_partitions_store up and down our stack.
Another is that also have one off "caching" classes like CachingStaleStatusResolver, CachingInstanceQueryer,
CachingDataTimeResolver and perhaps others I do not know about that present a wide range of capabilities inconsistently.
Superficially it is annoying to have to thread time, storage_id, and dynamic_partitions_store around everywhere
and hard to understand what class to use when interrogating the asset graph.

This belies a more profound problem: Some of our capabilities respect current time; some do not. Some of our
capabilities respect storage_id; some do not. That means the engineers do not know what reads are volatile
with respect to time and underlying storage, and you cannot know what is true versus not. It is also difficult
to know what is to safe to cache or not. This means also that as an engineer navigates the state of the asset
graph, it is difficult to know what operations are cheap to compute, versus potentially extremely
expensive to compute.

This RFC proposes not just Reactive Scheduling, but more principled taxonomy for modeling time and state
in our system, and new abstractions to interact with our system using that taxonomy. It then introduces
a new core abstraction, the AssetGraphView, that reifies that mental model in our codebase. The proposal
would be to retrofit AMP, reactive scheduling, the asset backfill daemon, and the dagster-webserver
to use this new abstraction. The following is a taxonomy of new terms a restatement of our
old terms in one spot.

Glossary/Taxonomy:
 * Asset (Definition) Graph: A stateless respresentation of the asset graph. Composed of
   user definitions and can be constructed without access to underlying state in the instance. 
   Considered a definition. This can be serialized to a snapshot.
 * Asset Graph View: A stateful representation of an asset definition graph at a particular
   point in time. Returns partitions spaces and asset slices.
 * Asset Partition: A single partition attached of an asset.
 * Zone of control: The subset of the asset graph that is under the control by a cooperating group
   of reactive scheduling sensors. Current the only subset supported is the code location but we may
   extend that definition to be cross-code-location in the future, or to be a subset of a 
   code location (perhaps asset group).
 * (Asset) Partition Space: A set of asset partition within the asset graph at a particular point in time
   tied to a particular state of the event log. We use the term "space" rather than "asset graph"
   deliberately as its tied an effective date and a state of the event log.. This is our "partition-native"
   API for subsystems such as reactive scheduling and asset backfills where the programmer must
   be be thinking in terms of traversing a multi-dimensional partition space at a particular
   point in time.
 * Asset Partition Slice: A slice of an single asset in the context of a partition space. 
 * (Definition) Snapshot: A serialized representation of a definition.
 * Code Version: A particular version of asset definition (tied to the code version of the underlying op)
    Explicitly provided by user (e.g. a hash of a sql statement or a container image containing business
    logic). Definitions without explict user-provided code version are considered "unversioned". Any
    entry produced by an asset is assigned this code version. If the definition is unversioned, 
    a hidden "system" code version is applied to the entry.
 * Asset (Partition) Materialization: A materialization of an asset partition. This is an entry in the event
   log corresponds to a potential modification of underlying state of the asset partition.
   Note: In the rest of this glosary "materialization" is shorthand for "asset partition materialization".
 * Asset (Partition) Observation: An observation of an asset partition. This entry in the event log
   means the read of an underlying asset partition at particular point in time.
   Note: In the rest of this glosary "observation" is shorthand for "asset partition observation".
 * Asset (Partition) Entry: An entry in the event log for an asset partition. Currently can be a
   materialization or observation. An entry indicates that a materialization *exists* at a
   particular point in time, but we do not know the conditions under which it was materialized.
   Note: In the rest of this glosary "entry" is shorthand for "asset partition entry".
 * Data Version: The version applied to an asset partition entry. This can always be explicitly
   provided by the user. For materializations, this can be system-provided by combining the
   code version of the current definition with the data version of the upstream entries.
 * Unsynced (Asset Partition): An asset partition's can be out of sync if its underlying most
   recent entry out of sync with its definition and upstream definitions and upstream persisted
   entries. If unsynced, rematerialization of the asset partition may result in a different value.
   If synced, rematerialization will definitivieliy result in the same value, assuming the user
   has abided by the contract that assets are idempotent with respect to versioning. An asset
   partition becomes unsynced if:
      * Meaningfully new code (defined as a new code version) has been pushed for the definition. Therefore
        re-materialization could could result in a different materialized value.
      * There is no materialization for this asset partition. Re-materialization will produce a new value.
      * The asset partition is out of sync if one of its parent asset partitions in is an updated state from its perspective.
        This means that the most recent materialization of the parent asset partition was not used to produce the most recent
        materialization. Re-materialization could result in a value since the upstream partitions have updated since the
        last materialization.
      * Upstream dependencies have changed.
      * There is an upstream asset partition that is unsynced, provided that upstream asset is
        within the scheduling zone. Put another way unsynced state is transitively determined within
        a scheduling zone. The rationale is that we communicate unsynced state if the user has
        the possibility of resolving it operationally.

    A "sync" is applied an entire zone of control to get a particular set of asset partitions into a synced state.

    Critically, definitions are built so that "sync" operations are idempotent with respect to code version and
    upstream data versions, which enables the system omit unnecessary computations and materializations.

  * Parent (Asset Partition) Updated: A parent asset partition can be in an *updated* state with respect to a child partition.
    An asset partition cannot be in an outdated state on its own: it is a relative state. A parent asset partition is an updated state
    if it has a new entry that was not used to compute the most recent materialization of the child asset partition.
    Example:

    B and C are children of A

    A --> B
    |
    ----> C

    t0: materialize(A, B, C)
       * B's perspective: A is not updated. Most recent materialization of A(t0) is used in B's most recent materialization B(t0)
       * C's perspective: A is not updated. Most recent materialization of A(t0) is used to C's most recent materialization C(t0)
    t1: materializize(A)
       * B's perspective: A is updated. Most recent materialization of A (t1) is not used in B's most recent materialization (t0)
       * C's perspective: A is updated. Most recent materialization of A (t1) is not used in C's most recent materialization (t0)
    t2: materialize(B)
       * B's perspective: A not updated. Most recent materialization of A (t1) is used in B's most recent materialization (t2)
       * C's perspective: A is updated. Most recent materialization of A (t1) is not used in C's most recent materialization (t0)
    t3: materialize(C)
       * B's perspective: A not updated. Most recent materialization of A (t1) is used in B's most recent materialization (t2)
       * C's perspective: A not updated. Most recent materialization of A (t1) is used in C's most recent materialization (t3)
  * New Parent Materialization: A new parent materialization is a materialization of a parent asset partition
    that is more recent. Example:
  * Effective time: The effective time over which you are evaluating an asset graph view. This is used
    for business logic such as determining the "latest partition window" for a time-windowed partition.
    All such operations much be done from the context of a particular point in time.
  * Last event ID: The event log is an immutable log of events, each has an event id, which
    is monotonically increasing. This allows us to evaluate the state of the asset graph with
    consistent state ignoring event log entries after this point.

Glossary Changelog Implications:

* Materialize Changed and Missing --> "Materialize Unsynced" or "Sync"
* Current time --> Effective time
* {storage_id, cursor} -> Last Event ID

** The Asset Graph View **

The asset graph view is partition-native view of the asset graph at a particular point in time (effective_dt) and
pinned to a particular state of the event log (last_event_id). Tis captured by a single object, the TemporalContext.

The asset graph think in terms of "asset slices". Asset slices are a successor to "ValidAssetSubset". They have
a number of differences with asset subsets, mostly stemming from the fact that they have a reference to the
AssetGraphView with which they are associated:

* Temporal-context aware: They slice represents a set of partitions on a single asset at a particular point in time.
* They abstract away passing around current_time, dynamic_partitions_store since those are properties. This results
  is substantially cleaner code.

Before:

```python
def get_parent_asset_subset(
    context, 
    asset_graph: AssetGraph,
    child_asset_subset: AssetSubset, 
    parent_key: AssetKey) -> AssetSubset:

    return asset_graph.get_parent_asset_subset(
        dynamic_partitions_store=context.instance_queryer,
        parent_asset_key=parent_asset_key,
        child_asset_subset=child_asset_subset,
        current_time=context.evaluation_dt,
    )
```

After
```
def get_parent_slice(child_slice: AssetSlice, parent_key: AssetKey) -> AssetSlice:
    return child_slice.get_parent_slice(parent_key)
```

* Are partition-native, in that they do not treat unpartitioned assets specially from an API perspective.
In effect an unpartitioned asset is an asset with a single partition whose partition_key is None. Slices
of unpartitioned assets either contain a single key or are empty. AssetSlice very deliberately does not
contain a property `is_partitioned` (although obviously one could infer it by breaking encapsulation). 


An materialized unpartitioned asset is an asset slice 
has a single time window from the beginning of time to the effective date. Statically partitions
also contain a single, complete time window. Time-partitioned assets 

In the end this allows one to construct a view and elegantly navigate the asset graph.

```python

asset_graph_view = AssetGraphView.build_for_test(
    defs=defs
    instance=DagsterInstance.get(),
    effective_dt=pendulum.now()
    last_event_id=None # None means volatile
)

asset_slice = asset_graph_view.get_asset_slice(asset_key=asset_key)

# The subset of the slice that is unsynced
asset_slice.compute_unsynced()
# This returns a slice representing all the unsynced asset partitions in the latest time window
asset_slice.latest_complete_time_window.compute_unsynced()
# Return upstream asset partitions (as a slice) updated since the last time "some_day_partition" was updated
asset_slice.compute_updated_parent_slice_of_partition("some_day_partition")
```

The above API is elegant enough to be easily executed within Python REPL. This has already been
extremely useful in debugging this prototype system 

The asset graph view and its related classes are the basis for making scheduling
evaluations.

Implications:
  * Rename AssetKeyPartitionKey to AssetPartition
  * All methods in the asset (definition) graph that interact with underlying storage should be moved.
    (e.g. get_partitions_in_range, get_parent_asset_subset) and hoisted into the AssetGraphView.
  * Understand what underlying storage we have which is not storage-id-aware. Determine if
    if it is ok to be volatile.

Future work:
  * Make this support multi-dimensional partitioning and dynamic partitioning
  * Develop pattern for prefetching data required by the asset graph view and then 
  offering guaranteed fast access properties.
  * Use the AssetGraphView in Asset Conditions/AMP, the Backfill Daemon, and the Webserver.
  * Formalize our time-windowing rules, taking advantage that we do not allow more than one
    time-windowing dimensions. We can treat all asset slices as time-windowed, in effect:
      * Unpartitioned asset slice: Have a single time window from the beginning of time to the effective date.
        We will call this the "complete time window".
      * Statically partitioned asset slice: Have a single, complete time window.
      * Time-partitioned asset slice: Represented by multiple time windows.
      * Multi-dimensional partitioned asset slice: If neither of the partition definitions within the
        multi-dimensional partition definition are themselves time-partitioned, then it has the complete
        time window. Multi-dimensional partitions can only have a single time-partitioned definition. In
        that case an asset slice backed by such a partition definition can have multiple time windows
        on that single dimension. 

    With the above conceptualization of time windows across all slices, this will provide the opportunity
    to have a *storage* schemes around time windows that can apply uniformly across all asset slices,
    which would enable much more efficient storage and retrieval of asset slices.
"""


# TODO: make abstract
class SchedulingPolicy:
    def __init__(
        self, sensor_spec: Optional["SensorSpec"] = None, expr: Optional["ExprNode"] = None
    ):
        self.sensor_spec = sensor_spec
        self.expr = expr

    def schedule_launch(
        self, context: "SchedulingExecutionContext", asset_slice: "AssetSlice"
    ) -> ScheduleLaunchResult:
        """If there is a sensor spec, this gets evaluated on every tick."""
        ...

    # defaults to honoring expr or empty if there is no expr
    def evaluate(
        self, context: "SchedulingExecutionContext", current_slice: "AssetSlice"
    ) -> EvaluationResult:
        """Evaluate gets called as the scheduling algorithm traverses over the partition space in context."""
        return EvaluationResult(
            asset_slice=self.expr.evaluate(context, current_slice)
            if self.expr
            else context.slice_factory.empty(current_slice.asset_key)
        )

    @staticmethod
    def for_expr(expr: "ExprNode"):
        return SchedulingPolicy(expr=expr)


class AssetSchedulingInfo(NamedTuple):
    asset_key: AssetKey
    scheduling_policy: Optional[SchedulingPolicy]
    partitions_def: Optional[PartitionsDefinition]

    def __repr__(self) -> str:
        return f"AssetSchedulingInfo(asset_key={self.asset_key}, scheduling_policy={self.scheduling_policy}, partitions_def={self.partitions_def})"


class SchedulingExecutionContext(NamedTuple):
    asset_graph_view: "AssetGraphView"
    # todo remove default
    previous_cursor: Optional[str] = None

    @staticmethod
    def create(
        instance: "DagsterInstance",
        repository_def: "RepositoryDefinition",
        effective_dt: datetime,
        last_event_id: Optional[int],
        # todo  remove default
        previous_cursor: Optional[str] = None,
    ) -> "SchedulingExecutionContext":
        from dagster._core.definitions.internal_asset_graph import InternalAssetGraph
        from dagster._core.reactive_scheduling.asset_graph_view import (
            AssetGraphView,
            TemporalContext,
        )

        stale_status_resolver = CachingStaleStatusResolver(instance, repository_def.asset_graph)
        # create these on demand rather than the lazy BS
        check.invariant(stale_status_resolver.instance_queryer)
        check.inst(stale_status_resolver.asset_graph, InternalAssetGraph)
        return SchedulingExecutionContext(
            asset_graph_view=AssetGraphView(
                temporal_context=TemporalContext(
                    effective_dt=effective_dt, last_event_id=last_event_id
                ),
                stale_resolver=stale_status_resolver,
            ),
            previous_cursor=previous_cursor,
        )

    @property
    def effective_dt(self) -> datetime:
        return self.asset_graph_view.temporal_context.effective_dt

    @property
    def last_event_id(self) -> Optional[int]:
        return self.asset_graph_view.temporal_context.last_event_id

    def empty_slice(self, asset_key: AssetKey) -> "AssetSlice":
        return self.slice_factory.empty(asset_key)

    @property
    def slice_factory(self) -> "AssetSliceFactory":
        return self.asset_graph_view.slice_factory

    @property
    def queryer(self) -> "CachingInstanceQueryer":
        return self.asset_graph_view.stale_resolver.instance_queryer

    @property
    def instance(self) -> "DagsterInstance":
        return self.queryer.instance

    @property
    def asset_graph(self) -> "InternalAssetGraph":
        from dagster._core.definitions.internal_asset_graph import InternalAssetGraph

        check.inst(self.asset_graph_view.stale_resolver.asset_graph, InternalAssetGraph)
        assert isinstance(self.asset_graph_view.stale_resolver.asset_graph, InternalAssetGraph)
        return self.asset_graph_view.stale_resolver.asset_graph

    def get_scheduling_info(self, asset_key: AssetKey) -> AssetSchedulingInfo:
        assets_def = self.asset_graph.get_assets_def(asset_key)
        return AssetSchedulingInfo(
            asset_key=asset_key,
            scheduling_policy=assets_def.scheduling_policies_by_key.get(asset_key),
            partitions_def=assets_def.partitions_def,
        )
