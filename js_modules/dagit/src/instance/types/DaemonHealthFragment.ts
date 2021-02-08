// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: DaemonHealthFragment
// ====================================================

export interface DaemonHealthFragment_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface DaemonHealthFragment_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: DaemonHealthFragment_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface DaemonHealthFragment_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string | null;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: DaemonHealthFragment_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface DaemonHealthFragment {
  __typename: "DaemonHealth";
  allDaemonStatuses: DaemonHealthFragment_allDaemonStatuses[];
}
