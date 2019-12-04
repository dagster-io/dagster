import path from "path";
import { PIPELINE_EXPLORER_ROOT_QUERY } from "../../PipelineExplorerRoot";
import { CachedGraphQLRequest } from "../MockedApolloLinks";

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
  variables: { pipeline: name, parentHandleID: "" },
  filepath: path.join(dataDir, `${name}.json`)
}));

// Composite rendering
MOCKS.push({
  name: "airline_demo_ingest_pipeline_composite",
  query: PIPELINE_EXPLORER_ROOT_QUERY,
  variables: {
    pipeline: "airline_demo_ingest_pipeline",
    parentHandleID: "master_cord_s3_to_df"
  },
  filepath: path.join(dataDir, `airline_demo_ingest_pipeline_composite.json`)
});

// Fan in out which triggers "wrapping" of DAG nodes
MOCKS.push({
  name: "fan_in_fan_out_pipeline",
  query: PIPELINE_EXPLORER_ROOT_QUERY,
  variables: { pipeline: "fan_in_fan_out_pipeline", parentHandleID: "" },
  filepath: path.join(dataDir, `fan_in_fan_out_pipeline.json`),
  repo: "examples/dagster_examples/toys"
});
