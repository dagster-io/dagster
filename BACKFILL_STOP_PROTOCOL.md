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
contract. Unmarked backfills retain legacy cancellation semantics and do not acquire the
worker-ledger guarantee. Automatic retries still preserve backfill lineage and
check status, and reserved owner/version tags become immutable independently of
opt-in. This prevents retrospective reparenting from bypassing admission. The
version boundary prevents unrecorded legacy dispatches from being mistaken for
never-started work.

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

Dispatch states are `PENDING -> ACKNOWLEDGED -> RESOLVED`. Logical `RUN` and `STEP`
dispatches are admitted before their external call and acknowledged after its
successful return. A physical `CHILD` receipt is admitted before a controller's
worker creation can persist; its retained resource supplies the acknowledgement
witness. Resolution requires definitive exit/nonexecution evidence. Resolved rows
remain as deduplication tombstones. A logical parent may resolve with a pending
child: that child still independently belongs to U(B).

Automatic child registration also has a unique retry intent, derived from the
failed parent's run ID. The native retry number is accounting metadata; group size
can change between consumers and does not identify a retry intent. The intent is stored independently
of mutable tags. Under the same backfill lock, registration returns the existing
child for that intent instead of inserting another run. Native `create_run` already
returns the run supplied by storage, so callers receive that canonical child.
Independent manual reexecution omits the automatic intent.

The worker target is persisted before dispatch. Supported Kubernetes targets name
the namespace, Job, and required admission-webhook binding. The required binding
field rejects a v1 K8s adapter constructing the target against a v2 core before
dispatch; it has no compatibility default. A typed `ChildWorkerTarget` also names its logical parent;
its `K8sPodWorkerTarget` records the AdmissionReview UUID, fixed Pod name,
namespace, and owning Job name/UID. An unknown target identifies its adapter and
cannot supply exit proof. Adapter status, run status, and worker-exit evidence are distinct types.

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
| Admit physical child | B is open, the run is nonterminal, and its RUN/STEP parent is unresolved; insert CHILD/PENDING under the same gate. An identical pending receipt replays its original admission even after closure or parent resolution; ACKNOWLEDGED/RESOLVED replay is denied. |
| Acknowledge dispatch | Exact claim exists and is pending; successful logical dispatch return or retained physical creation witness; persist `ACKNOWLEDGED`. |
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
5. Terminalize a remaining run record after its run-worker attempt has stopped.
   Remote step claims remain a separate finalization barrier. Atomically attempt
   finalization; otherwise continue draining.

For Kubernetes Jobs, foreground deletion and an empty Pod list are insufficient:
the Job controller can already have issued a Pod CREATE that has not persisted.
The Kubernetes garbage-collection contract explicitly excludes concurrent owner
deletion/child creation from its foreground-cache guarantee. The physical receipt
closes this gap; Job absence alone never establishes aggregate cancellation.

`BackfillPodAdmission` runs as a fail-closed mutating Pod admission webhook. The
run launcher and step handler protect Job/Pod-template owner, protocol, routing,
and logical-dispatch metadata. Before admitting a new child, the webhook checks
the live owning Job UID and its persisted logical target, then calls the atomic
child-admission command. It patches a unique fixed Pod name, admission identity,
and retaining finalizer before allowing persistence. Dry-run writes no receipt.

`reinvocationPolicy: Never` is part of this contract: Kubernetes generates a fresh
AdmissionReview UUID for each webhook invocation. An identical pending callback
continues one original admission. A new HTTP CREATE gets a new UUID/claim and must
win the gate again. Setting the fixed name before storage disables generated-name
storage retries; one request cannot acknowledge an old Pod then recreate that
receipt's name through another persistence attempt.

A pending absent child cannot resolve. The finalizer keeps a persisted child
observable until Dagster acknowledges it and observes definitive exit. The Pod
adapter verifies all protected metadata and the owning Job UID. Supported workers
use `restartPolicy: Never`, with no per-container restart policies/rules or native
restarting init sidecars. Kubernetes Job replacement and Dagster retries still
work: each replacement Pod receives its own admission receipt. No containers may
be added outside this dispatch contract after admission.

Definitive Pod evidence is either terminal phase plus Terminated status for every
declared main/init/ephemeral container, or a deleting Pod with no node assignment.
The latter cannot bind later because Kubernetes BindingREST checks the deletion
timestamp atomically with assigning nodeName. Mere phase, missing status, node
loss, an expired timeout, or a requested deletion is insufficient evidence.

After exit proof, Dagster removes only its own finalizer with UID and resourceVersion
JSONPatch preconditions, then resolves the acknowledged receipt in SQL. A crash
between these operations leaves an acknowledged receipt for reconciliation;
normal absence of its uniquely admitted resource now proves exit. Cleanup precedes
resolution, so no scan of resolved cleanup tombstones is required. Finalization
still requires every logical Job and physical Pod receipt to be resolved.

These conclusions rely on the native Kubernetes v1.35 implementations of
[admission UUID creation](https://github.com/kubernetes/kubernetes/blob/v1.35.0/staging/src/k8s.io/apiserver/pkg/admission/plugin/webhook/request/admissionreview.go),
[mutating admission before create](https://github.com/kubernetes/kubernetes/blob/v1.35.0/staging/src/k8s.io/apiserver/pkg/endpoints/handlers/create.go),
[fixed-name storage and finalizer retention](https://github.com/kubernetes/kubernetes/blob/v1.35.0/staging/src/k8s.io/apiserver/pkg/registry/generic/registry/store.go),
and [Pod binding](https://github.com/kubernetes/kubernetes/blob/v1.35.0/pkg/registry/core/pod/storage/storage.go).
The foreground limitation is documented in the
[Kubernetes garbage-collection contract](https://kubernetes.io/docs/concepts/architecture/garbage-collection/#foreground-cascading-deletion).

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
dispatch records its claim before its first external call. Each Job-controller
Pod persistence is preceded by a child receipt from admission. A failure before commit
issues no external call. A failure after commit leaves the claim pending. A crash,
retry-consumer replay, or queue retry cannot remove or repeat the claim because its
identity remains durable, including after resolution. This is at-most-once dispatch,
not exactly-once successful worker creation.

**I4: Ambiguity cannot become exit proof.** `PENDING` cannot be resolved. The adapter
acknowledges after the logical call completes or after observing a retained physical
creation witness, and UNKNOWN cannot resolve
an acknowledged attempt. Thus a delayed RPC, a lost response, or a vanished parent
cannot produce the premise used to remove a potentially live dispatch from U(B).

**I5: Final cancellation implies no owned live worker.** Assume every worker launch
uses I3 and every adapter's definitive evidence contract is sound. Any live owned
worker has an admitted dispatch by I3. Its dispatch cannot be resolved while that
worker exists by I4 and the adapter contract, so it belongs to U(B). A controller Pod admitted before closure
but persisted afterward also has its pending CHILD receipt in U(B); resolving its
Job cannot remove that barrier. New controller admission loses against closure or
parent resolution on the same backfill lock. Finalization
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
rewrite successful partition materializations. Final asset accounting runs after worker drainage and includes events visible at
that observation. The worker protocol does not fence already-issued external RPCs
or claim that an in-flight database request cannot commit an event later.

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
| Admitted Pod callback held before persistence | Pending CHILD blocks finalization even after Job deletion and parent resolution. |
| Pod persists before acknowledgement | Retaining finalizer preserves the identity/creation witness. |
| Child exits; cleanup fails or its response is lost | ACKNOWLEDGED receipt remains unresolved; reconciliation retries identity-checked cleanup. |
| Finalizer removed, before resolution commit | ACKNOWLEDGED receipt persists; unique admitted name cannot be recreated by this request. Reconcile exit/absence and resolve. |
| After exit, before logical resolution commit | Repeated definitive observation may resolve the same claim. |
| After resolution, before finalization | Tombstone prevents redispatch; a later tick finalizes. |
| Concurrent stop and registration/dispatch | Shared serialization chooses admitted-and-tracked or rejected. |

Safety is unconditional with respect to process crashes under the protocol premises.
Liveness is conditional: storage and adapters eventually respond, every admitted
dispatch reaches `ACKNOWLEDGED` or receives evidence-backed administrative repair,
workers eventually exit, and drain ticks are fair. An interrupted acknowledgement
does not recover automatically merely because the original external call returned.
Once closure commits the admitted set cannot grow; callback replay can only
continue persistence of an existing pending child. Liveness additionally requires
eventual definitive exit/nonexecution witnesses. For example, kubelet can leave
never-started containers Waiting after init failure; the conservative all-container
witness does not automatically resolve such a receipt. Honest pending status is
part of this safety contract, not proof that an execution process remains alive. Under those assumptions every
unresolved attempt eventually resolves and finalization succeeds. An ambiguous
attempt may keep cancellation pending indefinitely; timeout alone is not repair.
Operator repair requires evidence about the exact target and dispatch process,
not merely a run's terminal status.

## Adoption and compatibility

The guarantee starts only after all run creators, dispatchers, queue daemons,
executors, workers, API processes, and storage implementations use the protocol.
Unsupported storage or adapters must not silently supply weaker evidence.

The initial rollout requires quiescing producers and dispatchers, draining existing
backfills/workers, applying migrations through `7f812ac46e90` (physical-child schema), starting every
component on the matching v2 distribution, and installing/verifying the TLS Pod
admission service and fail-closed webhook, then enabling the protocol for new backfills. Existing
detached children or legacy in-flight attempts
require explicit inventory and repair before claiming the guarantee. A live mixed
version rollout cannot establish I2 or I3. Rollback likewise requires draining or
retaining protocol readers; older actors cannot safely ignore the dispatch ledger.
The feature defaults off upstream. Sol's package and admission-infrastructure prerequisites retain the default-off
policy; a separate activation change enables it after the coordinated upgrade. Disabling creation of new protocol backfills does not detach
or weaken the guarantees of already-marked backfills.

Kubernetes evidence assumes the normal authenticated kubelet/controller resource
lifecycle, durable API storage, stable admission configuration, and trusted namespace
operators. Other mutators must preserve protocol metadata/finalizer and must not
introduce unadmitted execution or container restarts. The launcher's configuration
preflight checks routing, CREATE rules, namespace coverage, fail-closed behavior,
absence of match-condition exclusions, and the v2 contract; administrators must
maintain that configuration for the lifetime of marked work. Forced API deletion, untracked manual recreation, and executing workers
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
| `SqlRunStorage.admit_backfill_worker_child` | Physical receipt/replay admission serialized against closure and parent resolution. |
| `SqlRunStorage.update_backfill` | Stale-write fence and atomic stop finalization with complete aggregate data. |
| `RunLauncherMethods.launch_run` and queued dequeue | Claim before `RUN_STARTING`, dispatch, then acknowledge. |
| `StepDelegatingExecutor._launch_step` | Gate remote step attempts, including native step retries. |
| `MultiprocessExecutor.execute` | Gate child-process start; acknowledge at the first process-object yield after `process.start()`. |
| `reconcile_backfill_worker_launches` | Drain durable targets using typed launcher evidence. |
| `K8sRunLauncher` and `K8sStepHandler` | Protected Job metadata, webhook/policy preflight, UID-fenced stop and physical Pod evidence/finalizer cleanup. |
| `BackfillPodAdmission` | Validate Pod/Job identity and commit CHILD before allowing Pod persistence. |
| `AdmissionServer` | Bounded TLS AdmissionReview transport; no worker arguments or credentials in diagnostics. |

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
Kubernetes Job/Pod identity and namespace, held admission before/after decision,
parent-resolution contention, callback replay, retained witness and cleanup crash
intervals, dry-run/configuration exclusions, preserved materializations, and full
native before/after reproduction. Real worker tests run locally, outside CI.
Reproduction scripts must pin package/base revisions, record module and artifact
hashes, retain native events and GraphQL results, and verify process/resource cleanup.
