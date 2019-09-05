import path from "path";
import { ROOT_PIPELINES_QUERY } from "../App";
import { TYPE_EXPLORER_CONTAINER_QUERY } from "../typeexplorer/TypeExplorerContainer";
import { TYPE_LIST_CONTAINER_QUERY } from "../typeexplorer/TypeListContainer";
import { PIPELINE_EXPLORER_ROOT_QUERY } from "../PipelineExplorerRoot";
import { CachedGraphQLRequest } from "./MockedApolloLinks";
import { RUNS_ROOT_QUERY } from "../runs/RunsRoot";
import { PIPELINE_EXECUTION_ROOT_QUERY } from "../execute/PipelineExecutionRoot";
import { ENABLED_FEATURES_ROOT_QUERY } from "../FlaggedFeature";
import { VERSION_QUERY } from "../VersionLabel";

export const MOCKS: CachedGraphQLRequest[] = [
  {
    name: "ROOT_PIPELINES_QUERY",
    query: ROOT_PIPELINES_QUERY,
    variables: undefined,
    filepath: path.join(__dirname, "__data__", "ROOT_PIPELINES_QUERY.json")
  },
  {
    name: "PIPELINE_EXPLORER_ROOT_QUERY",
    query: PIPELINE_EXPLORER_ROOT_QUERY,
    variables: { name: "airline_demo_ingest_pipeline" },
    filepath: path.join(
      __dirname,
      "__data__",
      "PIPELINE_EXPLORER_ROOT_QUERY_airline.json"
    )
  },
  {
    name: "PIPELINE_EXPLORER_ROOT_QUERY",
    query: PIPELINE_EXPLORER_ROOT_QUERY,
    variables: { name: "pandas_hello_world_pipeline" },
    filepath: path.join(
      __dirname,
      "__data__",
      "PIPELINE_EXPLORER_ROOT_QUERY_pandas.json"
    )
  },
  {
    name: "TYPE_EXPLORER_CONTAINER_QUERY",
    query: TYPE_EXPLORER_CONTAINER_QUERY,
    variables: {
      pipelineName: "airline_demo_ingest_pipeline",
      runtimeTypeName: "DataFrame"
    },
    filepath: path.join(
      __dirname,
      "__data__",
      "TYPE_EXPLORER_CONTAINER_QUERY.json"
    )
  },
  {
    name: "TYPE_LIST_CONTAINER_QUERY",
    query: TYPE_LIST_CONTAINER_QUERY,
    variables: {
      pipelineName: "airline_demo_ingest_pipeline"
    },
    filepath: path.join(__dirname, "__data__", "TYPE_LIST_CONTAINER_QUERY.json")
  },
  {
    name: "PIPELINE_EXECUTION_ROOT_QUERY",
    query: PIPELINE_EXECUTION_ROOT_QUERY,
    variables: {
      name: "pandas_hello_world_pipeline",
      solidSubset: ["sum_solid", "sum_sq_solid"],
      mode: "default"
    },
    filepath: path.join(
      __dirname,
      "__data__",
      "PIPELINE_EXECUTION_ROOT_QUERY.json"
    )
  },
  {
    name: "RUNS_ROOT_QUERY",
    query: RUNS_ROOT_QUERY,
    variables: undefined,
    filepath: path.join(__dirname, "__data__", "RUNS_ROOT_QUERY.json")
  },
  {
    name: "ENABLED_FEATURES_ROOT_QUERY",
    query: ENABLED_FEATURES_ROOT_QUERY,
    variables: undefined,
    filepath: path.join(
      __dirname,
      "__data__",
      "ENABLED_FEATURES_ROOT_QUERY.json"
    )
  },
  {
    name: "VERSION_QUERY",
    query: VERSION_QUERY,
    variables: undefined,
    filepath: path.join(__dirname, "__data__", "VERSION_QUERY.json")
  }
];
