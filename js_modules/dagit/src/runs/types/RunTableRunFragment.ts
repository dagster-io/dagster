// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunTableRunFragment
// ====================================================

export interface RunTableRunFragment_pipeline_UnknownPipeline {
  __typename: "UnknownPipeline";
  name: string;
}

export interface RunTableRunFragment_pipeline_Pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface RunTableRunFragment_pipeline_Pipeline {
  __typename: "Pipeline";
  name: string;
  solids: RunTableRunFragment_pipeline_Pipeline_solids[];
}

export type RunTableRunFragment_pipeline = RunTableRunFragment_pipeline_UnknownPipeline | RunTableRunFragment_pipeline_Pipeline;

export interface RunTableRunFragment_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  stepsSucceeded: number;
  stepsFailed: number;
  startTime: number | null;
  endTime: number | null;
  expectations: number;
  materializations: number;
}

export interface RunTableRunFragment_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type RunTableRunFragment_stats = RunTableRunFragment_stats_PipelineRunStatsSnapshot | RunTableRunFragment_stats_PythonError;

export interface RunTableRunFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunTableRunFragment {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  stepKeysToExecute: string[] | null;
  canCancel: boolean;
  mode: string;
  environmentConfigYaml: string;
  pipeline: RunTableRunFragment_pipeline;
  stats: RunTableRunFragment_stats;
  tags: RunTableRunFragment_tags[];
}
