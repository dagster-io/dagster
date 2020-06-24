import path from "path";
import { PIPELINE_EXPLORER_ROOT_QUERY } from "../../PipelineExplorerRoot";
import { CachedGraphQLRequest } from "../MockedApolloLinks";
import { PipelineExplorerRootQueryVariables } from "../../types/PipelineExplorerRootQuery";

const dataDir = path.join(__dirname, "__data__");

// Top level rendering of these pipelines
export const MOCKS: CachedGraphQLRequest[] = [
  "airline_demo_ingest_pipeline",
  "airline_demo_warehouse_pipeline",
  "composition",
  "log_spew",
  "many_events"
].map(name => ({
  name: name,
  query: PIPELINE_EXPLORER_ROOT_QUERY,
  variables: {
    pipelineSelector: {
      pipelineName: name,
      repositoryLocationName: "<<in_process>>",
      repositoryName: "internal_dagit_repository"
    },
    rootHandleID: "",
    requestScopeHandleID: ""
  } as PipelineExplorerRootQueryVariables,
  filepath: path.join(dataDir, `${name}.json`)
}));

// Composite rendering
MOCKS.push({
  name: "airline_demo_ingest_pipeline_composite",
  query: PIPELINE_EXPLORER_ROOT_QUERY,
  variables: {
    pipelineSelector: {
      pipelineName: "airline_demo_ingest_pipeline",
      repositoryLocationName: "<<in_process>>",
      repositoryName: "internal_dagit_repository"
    },
    rootHandleID: "master_cord_s3_to_df",
    requestScopeHandleID: "master_cord_s3_to_df"
  } as PipelineExplorerRootQueryVariables,
  filepath: path.join(dataDir, `airline_demo_ingest_pipeline_composite.json`)
});

// Fan in out which triggers "wrapping" of DAG nodes
MOCKS.push({
  name: "fan_in_fan_out_pipeline",
  query: PIPELINE_EXPLORER_ROOT_QUERY,
  variables: {
    pipelineSelector: {
      pipelineName: "fan_in_fan_out_pipeline",
      repositoryLocationName: "<<in_process>>",
      repositoryName: "toys_repository"
    },
    rootHandleID: "",
    requestScopeHandleID: ""
  } as PipelineExplorerRootQueryVariables,
  filepath: path.join(dataDir, `fan_in_fan_out_pipeline.json`),
  // TODO: remove dependency on legacy_examples
  // https://github.com/dagster-io/dagster/issues/2653
  repo: "examples/legacy_examples/dagster_examples/toys"
});
