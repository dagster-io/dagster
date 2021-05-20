// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: QueueDaemonStatusQuery
// ====================================================

export interface QueueDaemonStatusQuery_instance_daemonHealth_daemonStatus {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string;
  healthy: boolean | null;
  required: boolean;
}

export interface QueueDaemonStatusQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  daemonStatus: QueueDaemonStatusQuery_instance_daemonHealth_daemonStatus;
}

export interface QueueDaemonStatusQuery_instance {
  __typename: "Instance";
  daemonHealth: QueueDaemonStatusQuery_instance_daemonHealth;
}

export interface QueueDaemonStatusQuery {
  instance: QueueDaemonStatusQuery_instance;
}
