import path from "path";
import { PIPELINE_EXPLORER_ROOT_QUERY } from "../../PipelineExplorerRoot";
import { CachedGraphQLRequest } from "../MockedApolloLinks";

const dataDir = path.join(__dirname, "__data__");

export const MOCKS: CachedGraphQLRequest[] = [
  "airline_demo_ingest_pipeline",
  "airline_demo_warehouse_pipeline",
  "composition",
  "log_spew",
  "many_events"
].map(name => ({
  name: name,
  query: PIPELINE_EXPLORER_ROOT_QUERY,
  variables: { name },
  filepath: path.join(dataDir, `${name}.json`)
}));

MOCKS.push({
  name: "fan_in_fan_out_pipeline",
  query: PIPELINE_EXPLORER_ROOT_QUERY,
  variables: { name: "fan_in_fan_out_pipeline" },
  filepath: path.join(dataDir, `fan_in_fan_out_pipeline.json`),
  repo: "examples/dagster_examples/toys"
});
