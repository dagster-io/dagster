# Backfill cancellation protocol QA

Run `scripts/test-backfill-cancellation-protocol.sh --checkout /path/to/dagster`.
Pass `--constraints /path/to/dependency-constraints.txt` from an evidence archive
to reproduce its registry dependency versions. Pass `--private-wheels /path/to/wheels`
to repeat the native acceptance with exactly one local core, GraphQL, and Kubernetes
wheel per package after source acceptance. No package or image is published.
Docker, Kind, kubectl, and uv are required; the wrapper selects isolated CPython3.14.6.

By default, the runner owns a unique disposable Kind cluster, an isolated kubeconfig, a local
PostgreSQL container, separate fixture databases, an isolated Python environment,
and source-built non-editable worker images. It records commands, package versions,
source hashes, raw local test results, worker inventories, and cleanup. Credentials
and TLS keys remain in mode-0600 temporary manifests. Publication evidence contains
whitelisted redacted copies, excluding environment files, Secret YAML, kubeconfig,
and serialized instance references or Job/Pod command specifications.

The DefaultRunLauncher native probe verifies closed admission and records CANCELING
when definitive worker-exit proof is unavailable. The distinct
`--allow-unproven-default-launcher` option accepts that observation; strict
`--expect-contained` alone still requires CANCELED.

Each source and private-wheel image runs three native Jobs cases with the v2
production Pod-admission mechanism. A scoped TLS service invokes
`BackfillPodAdmission.admit`; its controlled transport wraps the production
`AdmissionServer` without replacing storage or admission decisions. Every admitted
Pod receives a durable CHILD receipt, a deterministic admission identity, and the
retained worker finalizer. Run and step Jobs remain independent of each other.

- `normal` starts the run Pod and remote step Pod, requests native GraphQL cancellation,
  and requires all Jobs, worker Pods, and four launch receipts to drain before CANCELED.
- `held-after` holds the allowed step-Pod response after production admission commits
  its CHILD receipt. Native cancellation must remain CANCELING while that receipt is
  PENDING and the Pod is invisible. Releasing the response permits the in-flight CREATE;
  physical exit and finalizer cleanup must precede aggregate completion.
- `held-before` holds the step-Pod request before the admission decision. After native
  cancellation closes the owner, releasing the request must produce a denied decision
  and no late worker Pod. No permit or CHILD receipt is created for that request.

The transport hold is bounded below Kubernetes' admission timeout. Interrupted or
ambiguous admission leaves a PENDING receipt and requires evidence-backed operator
repair; the QA runner does not clear it by timeout. The admission service and its
mutating configuration remain present through each acceptance observation. The
configuration uses failurePolicy Fail, reinvocationPolicy Never, and the exact
routed-Pod selector validated by the production launcher.

The physical-exit observations assume normally functioning responsive nodes, kubelets,
and container runtimes, plus trusted stable admission configuration and no out-of-band
force deletion or mutation of reserved worker metadata/finalizers. An unassigned Pod
with deletionTimestamp cannot subsequently bind through Kubernetes BindingREST.
A bound Pod requires terminal phase and terminated container evidence before finalizer
removal. Unknown identity, creation, or exit evidence keeps the aggregate CANCELING.

The runner uses only its generated kubeconfig and explicit fixture resource names.
Pass `--existing-kind-cluster NAME` to reuse an explicitly authorized local Kind cluster
when capacity is occupied. The runner exports an isolated kubeconfig, uses the explicit
`kind-NAME` context, and creates fresh namespaces, webhook routes, and scoped RBAC with
a unique ownership label. It refuses to change existing names or delete resources without
that label. Cleanup deletes only those fixture resources and its PostgreSQL container;
the reused cluster remains present. Admission configuration and PostgreSQL are retained
if native failure cleanup cannot drain the namespace, so an operator can inspect and repair
the outstanding evidence. No finalizer is cleared by the QA harness.

The default mode deletes its owned Kind cluster and PostgreSQL container. Generated
constraints and evidence are runtime artifacts, not repository source. The local Kind
capacity must have a free slot before creating a new cluster.
