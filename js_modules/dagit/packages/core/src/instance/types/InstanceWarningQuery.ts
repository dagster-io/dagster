/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: InstanceWarningQuery
// ====================================================

export interface InstanceWarningQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceWarningQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: InstanceWarningQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_causes[];
}

export interface InstanceWarningQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: InstanceWarningQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface InstanceWarningQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  allDaemonStatuses: InstanceWarningQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface InstanceWarningQuery_instance {
  __typename: "Instance";
  daemonHealth: InstanceWarningQuery_instance_daemonHealth;
  hasInfo: boolean;
}

export interface InstanceWarningQuery_partitionBackfillsOrError_PythonError {
  __typename: "PythonError";
}

export interface InstanceWarningQuery_partitionBackfillsOrError_PartitionBackfills_results {
  __typename: "PartitionBackfill";
  backfillId: string;
}

export interface InstanceWarningQuery_partitionBackfillsOrError_PartitionBackfills {
  __typename: "PartitionBackfills";
  results: InstanceWarningQuery_partitionBackfillsOrError_PartitionBackfills_results[];
}

export type InstanceWarningQuery_partitionBackfillsOrError = InstanceWarningQuery_partitionBackfillsOrError_PythonError | InstanceWarningQuery_partitionBackfillsOrError_PartitionBackfills;

export interface InstanceWarningQuery {
  instance: InstanceWarningQuery_instance;
  partitionBackfillsOrError: InstanceWarningQuery_partitionBackfillsOrError;
}
