// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RunActionMenuFragment
// ====================================================

export interface RunActionMenuFragment_pipeline_UnknownPipeline {
  __typename: "UnknownPipeline";
  name: string;
  solidSelection: string[] | null;
}

export interface RunActionMenuFragment_pipeline_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  name: string;
  solidSelection: string[] | null;
  pipelineSnapshotId: string;
}

export type RunActionMenuFragment_pipeline = RunActionMenuFragment_pipeline_UnknownPipeline | RunActionMenuFragment_pipeline_PipelineSnapshot;

export interface RunActionMenuFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunActionMenuFragment {
  __typename: "PipelineRun";
  runId: string;
  rootRunId: string | null;
  pipeline: RunActionMenuFragment_pipeline;
  mode: string;
  canTerminate: boolean;
  tags: RunActionMenuFragment_tags[];
}
