/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector, StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SidebarOpGraphsQuery
// ====================================================

export interface SidebarOpGraphsQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface SidebarOpGraphsQuery_pipelineOrError_Pipeline_solidHandle_stepStats_SolidStepStatsConnection_nodes {
  __typename: "RunStepStats";
  runId: string;
  startTime: number | null;
  endTime: number | null;
  status: StepEventStatus | null;
}

export interface SidebarOpGraphsQuery_pipelineOrError_Pipeline_solidHandle_stepStats_SolidStepStatsConnection {
  __typename: "SolidStepStatsConnection";
  nodes: SidebarOpGraphsQuery_pipelineOrError_Pipeline_solidHandle_stepStats_SolidStepStatsConnection_nodes[];
}

export interface SidebarOpGraphsQuery_pipelineOrError_Pipeline_solidHandle_stepStats_SolidStepStatusUnavailableError {
  __typename: "SolidStepStatusUnavailableError";
}

export type SidebarOpGraphsQuery_pipelineOrError_Pipeline_solidHandle_stepStats = SidebarOpGraphsQuery_pipelineOrError_Pipeline_solidHandle_stepStats_SolidStepStatsConnection | SidebarOpGraphsQuery_pipelineOrError_Pipeline_solidHandle_stepStats_SolidStepStatusUnavailableError;

export interface SidebarOpGraphsQuery_pipelineOrError_Pipeline_solidHandle {
  __typename: "SolidHandle";
  stepStats: SidebarOpGraphsQuery_pipelineOrError_Pipeline_solidHandle_stepStats | null;
}

export interface SidebarOpGraphsQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  name: string;
  solidHandle: SidebarOpGraphsQuery_pipelineOrError_Pipeline_solidHandle | null;
}

export type SidebarOpGraphsQuery_pipelineOrError = SidebarOpGraphsQuery_pipelineOrError_PipelineNotFoundError | SidebarOpGraphsQuery_pipelineOrError_Pipeline;

export interface SidebarOpGraphsQuery {
  pipelineOrError: SidebarOpGraphsQuery_pipelineOrError;
}

export interface SidebarOpGraphsQueryVariables {
  selector: PipelineSelector;
  handleID: string;
}
