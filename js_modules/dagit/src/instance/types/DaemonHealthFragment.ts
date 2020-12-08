// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { DaemonType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: DaemonHealthFragment
// ====================================================

export interface DaemonHealthFragment_allDaemonStatuses {
  __typename: "DaemonStatus";
  daemonType: DaemonType;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatTime: number | null;
}

export interface DaemonHealthFragment {
  __typename: "DaemonHealth";
  allDaemonStatuses: DaemonHealthFragment_allDaemonStatuses[];
}
