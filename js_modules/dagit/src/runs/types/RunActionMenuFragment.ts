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
}

export interface RunActionMenuFragment_pipeline_Pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface RunActionMenuFragment_pipeline_Pipeline {
  __typename: "Pipeline";
  name: string;
  pipelineSnapshotId: string;
  solids: RunActionMenuFragment_pipeline_Pipeline_solids[];
}

export type RunActionMenuFragment_pipeline = RunActionMenuFragment_pipeline_UnknownPipeline | RunActionMenuFragment_pipeline_Pipeline;

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
