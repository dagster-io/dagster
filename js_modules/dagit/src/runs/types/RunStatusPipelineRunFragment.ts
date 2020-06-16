// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunStatusPipelineRunFragment
// ====================================================

export interface RunStatusPipelineRunFragment_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface RunStatusPipelineRunFragment {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  pipeline: RunStatusPipelineRunFragment_pipeline;
}
