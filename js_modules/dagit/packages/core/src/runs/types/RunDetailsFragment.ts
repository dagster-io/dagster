/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunDetailsFragment
// ====================================================

export interface RunDetailsFragment {
  __typename: "Run";
  id: string;
  startTime: number | null;
  endTime: number | null;
  status: RunStatus;
}
