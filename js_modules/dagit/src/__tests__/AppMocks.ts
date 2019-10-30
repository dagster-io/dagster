import path from "path";
import { ROOT_PIPELINES_QUERY } from "../App";
import { TYPE_EXPLORER_CONTAINER_QUERY } from "../typeexplorer/TypeExplorerContainer";
import { TYPE_LIST_CONTAINER_QUERY } from "../typeexplorer/TypeListContainer";
import { SOLIDS_ROOT_QUERY } from "../solids/SolidsRoot";
import { PIPELINE_EXPLORER_ROOT_QUERY } from "../PipelineExplorerRoot";
import { CachedGraphQLRequest } from "./MockedApolloLinks";

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
      "PIPELINE_EXPLORER_ROOT_QUERY.json"
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
    name: "SOLIDS_ROOT_QUERY",
    query: SOLIDS_ROOT_QUERY,
    variables: {},
    filepath: path.join(__dirname, "__data__", "SOLIDS_ROOT_QUERY.json")
  }
];
