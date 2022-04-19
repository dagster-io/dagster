/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: LastRunsWarningsFragment
// ====================================================

export interface LastRunsWarningsFragment_run {
  __typename: "Run";
  id: string;
  status: RunStatus;
}

export interface LastRunsWarningsFragment {
  __typename: "LatestRun";
  stepKey: string;
  run: LastRunsWarningsFragment_run | null;
}
