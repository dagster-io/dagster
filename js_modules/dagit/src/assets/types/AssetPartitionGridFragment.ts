// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetPartitionGridFragment
// ====================================================

export interface AssetPartitionGridFragment_runOrError_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError" | "PythonError";
}

export interface AssetPartitionGridFragment_runOrError_PipelineRun {
  __typename: "PipelineRun";
  pipelineSnapshotId: string | null;
}

export type AssetPartitionGridFragment_runOrError = AssetPartitionGridFragment_runOrError_PipelineRunNotFoundError | AssetPartitionGridFragment_runOrError_PipelineRun;

export interface AssetPartitionGridFragment {
  __typename: "AssetMaterialization";
  partition: string | null;
  runOrError: AssetPartitionGridFragment_runOrError;
}
