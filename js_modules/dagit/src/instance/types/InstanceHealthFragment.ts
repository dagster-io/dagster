// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { DaemonType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: InstanceHealthFragment
// ====================================================

export interface InstanceHealthFragment_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  daemonType: DaemonType;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatTime: number | null;
}

export interface InstanceHealthFragment_daemonHealth {
  __typename: "DaemonHealth";
  allDaemonStatuses: InstanceHealthFragment_daemonHealth_allDaemonStatuses[];
}

export interface InstanceHealthFragment {
  __typename: "Instance";
  daemonHealth: InstanceHealthFragment_daemonHealth;
}
