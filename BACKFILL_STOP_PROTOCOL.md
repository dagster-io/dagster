# Backfill close-and-drain protocol

## Problem and intended behavior

Dagster 1.13.26 and master `c97898c3e4a8a3cc5e32fcc2ca97aea810342ed9`
permit an automatic retry while its backfill is `CANCELING`. The retry retains
parent/root run ancestry but loses its backfill tags. A subsequent backfill tick
can report `CANCELED` while that retry remains `STARTED`.

The intended behavior is: close admission, stop and account for admitted work,
then report completion. Previously committed materializations remain valid.
The guarantee includes launcher-owned run workers and executor-owned step workers.
An arbitrary external process or service started by user asset code is outside
Dagster's worker-ownership contract.

Repeated reads of `REQUESTED` are insufficient. The execution
`read REQUESTED; commit CANCELING; submit` passes every read guard. Registration,
dispatch admission, closure, and finalization must share an atomic ordering.

## State and ownership

The protocol is explicitly enabled through instance configuration. Newly created
backfills retain a durable protocol-version tag; only marked backfills carry this
contract. Existing unmarked backfills retain released behavior. This boundary
prevents unrecorded legacy dispatches from being mistaken for never-started work.

For each protocol backfill B, define:

- `open(B)`: its status is exactly `REQUESTED`.
- `R(B)`: the durable set of registered owned runs, including automatic retries.
- `D(B)`: the durable set of admitted worker dispatches, each identified by
  `(run_id, worker_id)`. A retry of a step has a distinct worker identity.
- `U(B)`: dispatches whose state is not `RESOLVED`.

`RunsTable.backfill_id` is the authoritative run owner. Run-body and normalized
tag projections preserve that owner; mutable tag writes cannot detach an owned
run. The owning `BACKFILL_TAGS` constant defines the lineage tags copied explicitly
by automatic reexecution. Manual reexecution may deliberately create an independent
run with no backfill owner and is outside B's cancellation request.

The run also retains its protocol version at registration, so disabling creation
of new protocol backfills cannot downgrade existing run ownership. A missing owner
for such a run fails closed. Legacy orphan-tagged synchronous submissions retain
their released behavior only outside the protocol.

Dispatch states are `PENDING -> ACKNOWLEDGED -> RESOLVED`. A pending dispatch was
durably admitted before an external call. An acknowledged dispatch means that the
adapter returned successfully and finished issuing that attempt's launch requests.
A resolved dispatch means that the adapter supplied definitive evidence that all
workers belonging to that attempt have exited and no delayed launch can create
another worker. Resolved rows remain as deduplication tombstones.

Automatic child registration also has a unique retry intent, derived from the
failed parent's run ID. The native retry number is accounting metadata; group size
can change between consumers and does not identify a retry intent. The intent is stored independently
of mutable tags. Under the same backfill lock, registration returns the existing
child for that intent instead of inserting another run. Native `create_run` already
returns the run supplied by storage, so callers receive that canonical child.
Independent manual reexecution omits the automatic intent.

The worker target is persisted before dispatch. Supported Kubernetes targets name
the namespace and Job. An unknown target identifies its adapter and cannot supply
exit proof. Adapter status, run status, and worker-exit evidence are distinct types.

Protocol Kubernetes creation issues one logical POST through a dedicated client
with transport retries disabled. A lost response remains pending. Native creation
retries are retained only for legacy runs: a timed-out earlier POST can otherwise
recreate a Job after a later successful retry has been acknowledged and drained.

## Atomic commands

RunStorage exposes semantic commands, not transaction callbacks or SQL connections.
The SQL implementation uses explicit transactions, including on connections with
PostgreSQL AUTOCOMMIT, and locks the backfill row. SQLite uses a write transaction
that supplies the equivalent serialization. Lock ordering is backfill before run.

| Command | Preconditions and committed effect |
| --- | --- |
| Register owned run | B exists and is open; insert run and immutable owner atomically. Otherwise reject. |
| Claim worker dispatch | B is open; run belongs to B; worker identity has no prior claim; insert `PENDING` atomically. Run-worker claims additionally require a launchable run. |
| Acknowledge dispatch | Exact claim exists and is pending; adapter has returned successfully; persist `ACKNOWLEDGED`. |
| Request stop | Atomically close B by entering `CANCELING`; repeated stop is idempotent. Automatic teardown uses the same gate through `FAILING`. |
| Resolve dispatch | Exact claim is acknowledged and definitive adapter evidence exists. Run-worker resolution additionally requires a terminal run record. Persist `RESOLVED`. |
| Finish stop | B is closed, U(B) is empty, and all R(B) run records are terminal; atomically commit `CANCELED` or the corresponding failure completion. |
| Explicit resume | A separate, deliberate `FAILED -> REQUESTED` operation; ordinary progress writes cannot reopen closure. |

No transaction spans a launcher, executor, gRPC, broker, or Kubernetes call.
Cancellation does not prevent a pre-close admitted call from starting later. It
prevents that call from escaping accounting or from allowing premature completion.

Run launch, queue dequeue, and step dispatch all use this gate. Replayed retry
events reuse the native child link. An already-detached retry child is rejected,
not silently resubmitted or retrospectively reparented. Run-worker resume requires
a new durable attempt identity; an adapter that cannot supply one must reject it.

## Drain algorithm

1. Commit closure before attempting termination.
2. Cancel registered, unclaimed runs. This is safe even for `NOT_STARTED`: every
   worker-dispatch path now needs a claim, and closure prevents such a claim.
3. For admitted dispatches, ask the owning adapter to stop the worker resource.
   Continue inspecting both run and step targets, including step-specific namespaces.
4. Resolve only acknowledged dispatches with definitive exit evidence. A terminal
   run event, timeout, unavailable server, missing unacknowledged Job, or an empty
   parent-process inventory does not establish that evidence.
5. Terminalize remaining run records after the corresponding execution workers
   have stopped. Atomically attempt finalization; otherwise continue draining.

For a Kubernetes dispatch, a successful create acknowledgement bounds the set of
issued create requests. The stop adapter must account for the named Job and its
Pods. A live Job capable of creating another Pod prevents resolution, even if its
current Pods have exited. Deletion requires observing absence of that Job and all
its Pods; a definitive terminal Job requires observing that no execution Pod remains
live. Run labels and namespace must match the persisted target, and a present
Job's UID must match its Pods' owner references. Worker Job names are unique within
the attempt and cannot be recreated by another protocol dispatch. Separate
step Jobs have their own dispatch records; parent Pod exit is never their exit proof.

For other adapters, UNKNOWN remains unresolved. An empty gRPC run inventory alone
does not prove absence of multiprocess step children after an abrupt parent exit.
Adapters may implement stronger resource containment and evidence contracts without
changing the admission protocol.

## Invariants and arguments

**I1: Immutable ownership.** Every automatically created retry in R(B) has owner B,
with native run ancestry intact. Registration stores the owner and lineage together;
owner-preserving reads and writes prevent a stale mutable projection from dropping it.
Manual independent runs are a deliberate ownership boundary, not an exception to I1.

**I2: Closed admission.** After closure commits, no new run registration or dispatch
claim for B commits before an explicit valid resume. Registration, claims, closure,
and state updates serialize on the same backfill gate. A contender ordered before
closure is durably admitted; one ordered after closure sees closed and is rejected.
Stale progress writes cannot restore `REQUESTED`.

**I3: Every external worker launch has a durable claim.** Each native run and step
dispatch records its claim before its first external call. A failure before commit
issues no external call. A failure after commit leaves the claim pending. A crash,
retry-consumer replay, or queue retry cannot remove or repeat the claim because its
identity remains durable, including after resolution. This is at-most-once dispatch,
not exactly-once successful worker creation.

**I4: Ambiguity cannot become exit proof.** `PENDING` cannot be resolved. The adapter
acknowledges only after completing the dispatch call, and UNKNOWN cannot resolve
an acknowledged attempt. Thus a delayed RPC, a lost response, or a vanished parent
cannot produce the premise used to remove a potentially live dispatch from U(B).

**I5: Final cancellation implies no owned live worker.** Assume every worker launch
uses I3 and every adapter's definitive evidence contract is sound. Any live owned
worker has an admitted dispatch by I3. Its dispatch cannot be resolved while that
worker exists by I4 and the adapter contract, so it belongs to U(B). Finalization
requires U(B) empty atomically. Therefore a live worker contradicts finalization.
I2 prevents an additional post-finalization claim, and resolved tombstones prevent
reissuing a prior attempt. This argument includes remote step workers.

**I6: Replay cannot create an additional worker for the same attempt.** Composite
dispatch identity is unique. Only the transaction inserting a previously absent
claim authorizes the external call. Replays observe its pending, acknowledged,
or resolved record and do not redispatch. Retry policy may admit a new distinct
step attempt only while B remains open.

**I7: Materialization provenance survives stopping.** Stop commands modify control
state, worker records, and run status. They do not delete committed asset events or
rewrite successful partition materializations. Final asset accounting occurs after
the run/worker drain so its observation cannot omit a still-running producer's commit.

**I8: One automatic child per retry intent.** A unique persisted intent identifies
the failed parent. Concurrent registrations serialize under the backfill
gate and the uniqueness constraint prevents a second child even if callers use
different UUIDs. The later registration returns the stored child. Native retry
linking and attempt-level dispatch deduplication therefore refer to the same run.
Manual reexecution does not inherit an automatic intent.

These are inductive arguments about protocol transitions under the stated adapter
and deployment premises. Concurrency and fault-injection tests seek counterexamples;
they are not a machine-checked proof of every Python implementation.

## Crash cases and liveness

| Failure point | Recovery and safety result |
| --- | --- |
| Before registration/claim commit | Transaction rollback; no external dispatch authorized. |
| After claim commit, before or during RPC | Pending claim survives; stop remains pending. No redispatch. |
| Worker created, response lost | Pending claim remains ambiguous; no false completion. |
| Successful RPC, before acknowledgement commit | Same conservative pending outcome. |
| After acknowledgement, before worker exit | Adapter repeatedly stops/inspects the durable target. |
| After exit, before resolution commit | Repeated definitive observation may resolve the same claim. |
| After resolution, before finalization | Tombstone prevents redispatch; a later tick finalizes. |
| Concurrent stop and registration/dispatch | Shared serialization chooses admitted-and-tracked or rejected. |

Safety is unconditional with respect to process crashes under the protocol premises.
Liveness is conditional: storage and adapters eventually respond, every admitted
dispatch reaches `ACKNOWLEDGED` or receives evidence-backed administrative repair,
workers eventually exit, and drain ticks are fair. An interrupted acknowledgement
does not recover automatically merely because the original external call returned.
Once closure commits the admitted set cannot grow. Under those assumptions every
unresolved attempt eventually resolves and finalization succeeds. An ambiguous
attempt may keep cancellation pending indefinitely; timeout alone is not repair.
Operator repair requires evidence about the exact target and dispatch process,
not merely a run's terminal status.

## Adoption and compatibility

The guarantee starts only after all run creators, dispatchers, queue daemons,
executors, workers, API processes, and storage implementations use the protocol.
Unsupported storage or adapters must not silently supply weaker evidence.

The initial rollout requires quiescing producers and dispatchers, draining existing
backfills/workers, applying the storage migration, and starting every component on
the matching distribution, then enabling the protocol for new backfills. Existing
detached children or legacy in-flight attempts
require explicit inventory and repair before claiming the guarantee. A live mixed
version rollout cannot establish I2 or I3. Rollback likewise requires draining or
retaining protocol readers; older actors cannot safely ignore the dispatch ledger.
The feature defaults off upstream. Sol's adoption explicitly enables it after the
coordinated upgrade. Disabling creation of new protocol backfills does not detach
or weaken the guarantees of already-marked backfills.

Kubernetes evidence assumes the normal authenticated kubelet/controller resource
lifecycle. Forced API deletion, untracked manual recreation, and executing workers
on a partitioned node without definitive termination evidence are not proof of
absence. Operators must not bypass resource ownership or mark unknown attempts
resolved while such effects remain possible.

## Validation contract

The concrete implementation uses these seams:

| Component | Responsibility |
| --- | --- |
| `PartitionBackfill.uses_stop_protocol` | Authoritative version policy; unknown reserved versions fail explicitly. |
| `SqlRunStorage._core_add_run` | Atomic ownership/intent registration and canonical automatic child reuse. |
| `SqlRunStorage.claim_backfill_worker_launch` | Durable run/step dispatch admission under the backfill row lock. |
| `SqlRunStorage.update_backfill` | Stale-write fence and atomic stop finalization with complete aggregate data. |
| `RunLauncherMethods.launch_run` and queued dequeue | Claim before `RUN_STARTING`, dispatch, then acknowledge. |
| `StepDelegatingExecutor._launch_step` | Gate remote step attempts, including native step retries. |
| `MultiprocessExecutor.execute` | Gate child-process start; acknowledge at the first process-object yield after `process.start()`. |
| `reconcile_backfill_worker_launches` | Drain durable targets using typed launcher evidence. |
| `K8sRunLauncher` and `K8sStepHandler` | Immutable Kubernetes target/identity, launch and definitive resource-exit checks. |

The protocol currently rejects native same-run worker resume: an ambiguous original
run dispatch cannot safely authorize another dispatch. A distinct automatic retry
run is still governed by native retry policy and has its own owned run/attempt.
Unsupported executor adapters are rejected for marked runs before execution.
Native `StepLauncher` resources, including EMR/Databricks, do not yet implement
the dispatch receipt/target contract and are rejected before their launch call.
Kubernetes remote step execution uses the supported `StepDelegatingExecutor`
adapter. The legacy `forceSynchronousSubmission` GraphQL shortcut does not persist
a backfill owner; it is rejected when protocol creation is enabled. Ordinary
asynchronous submission is the canonical protocol path.

Tests must cover storage rollback, real SQLite and PostgreSQL contention, stale
state/owner writes, uniqueness/replay, missing/closed backfills, ordinary automatic
and manual retries, existing children, queue/direct run dispatch, remote step
dispatch and retry, every crash interval above, UNKNOWN versus definitive evidence,
Kubernetes Job/Pod identity and namespace, preserved materializations, and full
native before/after reproduction. Real worker tests run locally, outside CI.
Reproduction scripts must pin package/base revisions, record module and artifact
hashes, retain native events and GraphQL results, and verify process/resource cleanup.
