// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: RunLauncher
// ====================================================

export interface RunLauncher_instance_runLauncher {
  __typename: "RunLauncher";
  name: string;
}

export interface RunLauncher_instance {
  __typename: "Instance";
  runLauncher: RunLauncher_instance_runLauncher | null;
}

export interface RunLauncher {
  instance: RunLauncher_instance;
}
