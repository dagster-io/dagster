# Backfill cancellation protocol QA

Run `scripts/test-backfill-cancellation-protocol.sh --checkout /path/to/dagster`.
Pass `--constraints /path/to/dependency-constraints.txt` from an evidence archive
to reproduce its registry dependency versions. Pass `--private-wheels /path/to/wheels`
to repeat the real Kind acceptance with that local wheel set after source acceptance.
No package or image is published. Python, Docker, Kind, kubectl, and uv are required.

The runner owns a unique disposable Kind cluster, an isolated kubeconfig, a local
PostgreSQL container, separate fixture databases, an isolated Python environment,
and source-built non-editable worker images. It records commands, package versions,
source hashes, raw local test results, worker inventories, and cleanup. Credentials
remain in mode-0600 temporary files. The publication evidence contains redacted copies.

The DefaultRunLauncher native probe verifies closed admission and records `CANCELING`
when definitive worker-exit proof is unavailable. The real Kubernetes acceptance
starts independent run and remote-step Jobs/Pods, requests native GraphQL cancellation,
and requires physical worker drainage before `CANCELED`. Owner references from the step
Job to the parent Pod are disabled, so deleting the parent cannot substitute for
explicit step drainage. Node runtime container records provide an additional exit witness.

The Kubernetes proof assumes reachable control-plane APIs and normally functioning,
responsive nodes, kubelets, and container runtimes. It assumes no out-of-band force
deletion or mutation of the fixture Jobs/Pods. Under those conditions, terminal Pod
container states and completed ordinary deletion are evidence of physical exit.
API object absence cannot prove physical exit after forced deletion on an unreachable
node; this test does not establish safety for that fault model. Unknown or conflicting
identity evidence must keep the aggregate `CANCELING`.

The runner uses only its generated kubeconfig and explicit fixture resource names.
Cleanup deletes its namespace, Kind cluster, and PostgreSQL container. Existing clusters
and production configurations are outside its scope. Generated constraints and evidence
are runtime artifacts, not repository files.
