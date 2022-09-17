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
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface OverviewJobFragment {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  runs: OverviewJobFragment_runs[];
}
