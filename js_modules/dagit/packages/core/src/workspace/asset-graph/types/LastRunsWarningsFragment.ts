/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../../types/globalTypes";

// ====================================================
// GraphQL fragment: LastRunsWarningsFragment
// ====================================================

export interface LastRunsWarningsFragment_LatestRun_run {
  __typename: "Run";
  id: string;
  status: RunStatus;
}

export interface LastRunsWarningsFragment_LatestRun {
  __typename: "LatestRun";
  stepKey: string;
  run: LastRunsWarningsFragment_LatestRun_run | null;
}

export interface LastRunsWarningsFragment_JobRunsCount {
  __typename: "JobRunsCount";
  stepKey: string;
  jobNames: string[];
  count: number;
  sinceLatestMaterialization: boolean;
}

export type LastRunsWarningsFragment = LastRunsWarningsFragment_LatestRun | LastRunsWarningsFragment_JobRunsCount;
