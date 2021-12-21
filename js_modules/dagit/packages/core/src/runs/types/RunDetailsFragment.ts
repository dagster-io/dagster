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
  endTime: number | null;
  startTime: number | null;
  status: RunStatus;
}
