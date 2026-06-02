# dagster-rest-resources

This library exposes Dagster functionality as REST-style resources, primarily by wrapping Dagster's graphql API, with some exceptions (e.g., `artifact` makes requests directly to s3 and there may be other exceptions in the future).

## Code Organization

```
dagster-rest-resources/
├── api/                    # REST-style interface classes (used by consumers of the library)
│   ├── deployment.py
│   └── asset.py
├── queries/                # Graphql queries (used internally for code generation)
│   ├── deployment.graphql
│   └── asset.graphql
├── schemas/                # Pydantic response models (returned by API rest interface classes)
│   ├── deployment.py
│   └── asset.py
└── gql_client.py           # makes graphql calls
└── s3_client.py            # makes s3 calls
```

## Request Flow

```
                           ┌───────── dagster-rest-resources ───────-─┐
Library Consumer           │ API Layer                GraphQL Client  │          GraphQL API
      │                    │ (/api/asset.py)          (gql_client.py) │
      │                    │        │                        │        │              │
      │  call method with  │        │                        │        │              │
      │  parsed_args ──────────────>│                        │        │              │
      │                    │        │  send authed request   │        │              │
      │                    │        │  with parsed args ────>│        │              │
      │                    │        │                        │  /graphql             │
      │                    │        │                        │  request ────────────>│
      │                    │        │                        │        │              │
      │                    │        │                        │        │    /graphql  │
      │                    │        │                        │<─────────── response  │
      │                    │        │    parse response and  │        │              │
      │                    │        │<────────────── return  │        │              │
      │    transform response into  |                        │        │              │
      │ <─────── schema and return  │                        │        │              │
                           └──────────────────────────────────────────┘
```

## Adding/Updating a Resource

In this example, we'll implement a `run` resource.

### Step 1: Define/Update Queries

Write a graphql query against the API to retrieve the data/perform the mutation that backs your rest-style resource.

```graphql
# queries/run.graphql
query GetRun($runId: ID!) {
  runOrError(runId: $runId) {
    __typename
    ... on Run {
      runId
      status
      creationTime
      startTime
      endTime
      jobName
    }
    ... on RunNotFoundError {
      message
    }
    ... on PythonError {
      message
    }
  }
}
```

### Step 2: Generate Code

Make sure you have your root venv activated and run the codegen command from the root of the repo:

```bash
source .venv/bin/active
just py-graphql-codegen
```

This will scan the `/queries` directory and generate new type definitions, graphql queries, client methods, and so on, in the `/__generated__/` directory, according to the schema and your query changes.

### Step 3: Define Schema

Create new `DgApi*` pydantic models that your rest resource will transform the raw graphql responses into and return.

```python
# schemas/run.py
from pydantic import BaseModel

from dagster_rest_resources.schemas.enums import DgApiRunStatus


class DgApiRun(BaseModel):
    id: str
    status: DgApiRunStatus
    created_at: float
    started_at: float | None = None
    ended_at: float | None = None
    job_name: str | None = None
```

Note that generated enums are re-exported from `schemas/enums` so they can be given on-spec names for consumers of the library.
Another important thing is that any list schema should inherit from one of the `DgApiList` classes.

### Step 4: Create API Class and Unit Tests

These are the classes and methods consumers of the library will import and call.
The API class should call through to one (or, if necessary to assemble the resource, more) code-generated methods available on the client.
They should never make any ad-hoc queries.

Thanks to the code generation and type system, you can always account for every return type that can come back from the a generated graphql api request.

The methods must handle all possible return types from those queries, including errors.
Successful responses must be transformed into the schemas you defined in step 3.
Error responses must be wrapped in the appropriate `Exception`, given a descriptive message, and raised to the consumer.

```python
# api/run.py
@dataclass(frozen=True)
class DgApiRunApi:
    _client: IGraphQLClient

    def get_run(self, run_id: str) -> DgApiRun:
        result = self._client.get_run(run_id=run_id).run_or_error

        match result.typename__:
            case "Run":
                return DgApiRun(
                    id=result.run_id,
                    status=result.status,
                    created_at=result.creation_time,
                    started_at=result.start_time,
                    ended_at=result.end_time,
                    job_name=result.job_name,
                )
            case "RunNotFoundError":
                raise DagsterPlusGraphqlError(f"Run not found: {result.message}")
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching run: {result.message}")
            case _ as unreachable:
                # this will trigger a type error if any possible return type has not been handled
                assert_never(unreachable)
```

```python
# api_tests/test_run.py
def _make_run_result(
    run_id: str = "run-1",
    status: RunStatus = RunStatus.SUCCESS,
    creation_time: float = 1705311000.0,
    start_time: float | None = None,
    end_time: float | None = None,
    job_name: str = "test-job-1",
) -> GetRunRunOrErrorRun:
    return GetRunRunOrErrorRun(
        __typename="Run",
        runId=run_id,
        status=status,
        creationTime=creation_time,
        startTime=start_time,
        endTime=end_time,
        jobName=job_name,
    )


class TestGetRun:
    def test_returns_run(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run.return_value = GetRun(runOrError=_make_run_result())
        result = DgApiRunApi(client).get_run("run-1")

        client.get_run.assert_called_once_with(run_id="run-1")
        assert result == DgApiRun(
            id="run-1",
            status=RunStatus.SUCCESS,
            created_at=1705311000.0,
            started_at=None,
            ended_at=None,
            job_name="test-job-1",
        )

    def test_run_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run.return_value = GetRun(
            runOrError=GetRunRunOrErrorRunNotFoundError(__typename="RunNotFoundError", message="")
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Run not found"):
            DgApiRunApi(client).get_run("run-xyz")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run.return_value = GetRun(
            runOrError=GetRunRunOrErrorPythonError(__typename="PythonError", message="")
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching run"):
            DgApiRunApi(client).get_run("run-xyz")
```

```python
# api_tests/test_rest_compliance
ALL_API_CLASSES = [
    ...,
    DgApiRunApi,
    ...
]
```

Incidentally, coding agents have been pretty good at generating request/response boilerplate for unit tests, but have struggled to cover every logic path.
The rest compliance test just checks some basic naming and typing conventions.

## Naming Conventions

### API Classes

All API classes follow: `DgApi{Resource}Api`

- ✅ `DgApiDeploymentApi`
- ✅ `DgApiAssetApi`
- ✅ `DgApiRunApi`

### API Methods

REST-style method naming:

- `list_*` - Return multiple items
- `get_*` - Return single item by ID
- `create_*` - Create new resource
- `update_*` - Modify existing resource
- `delete_*` - Remove resource
- `action_*` - Any mutation that is not a create, update, or delete

### API Schemas

Pydantic models:

- `DgApi{Resource}` - Single resource model
- `DgApi{Resource}List` - List of resource models

## Authentication

Authentication is handled by consumers and the necessary parameters are passed to the library graphql client.
