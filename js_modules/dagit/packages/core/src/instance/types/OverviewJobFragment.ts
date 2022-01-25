/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: OverviewJobFragment
// ====================================================

export interface OverviewJobFragment_runs {
  __typename: "Run";
  id: string;
  mode: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface OverviewJobFragment_modes {
  __typename: "Mode";
  id: string;
  name: string;
}

export interface OverviewJobFragment {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  runs: OverviewJobFragment_runs[];
  modes: OverviewJobFragment_modes[];
}
