import {gql} from '../../apollo-client';

export const PARTITION_SET_FOR_BACKFILL_TABLE_FRAGMENT = gql`
  fragment PartitionSetForBackfillTableFragment on PartitionSet {
    id
    name
    mode
    pipelineName
    repositoryOrigin {
      id
      repositoryName
      repositoryLocationName
    }
  }
`;
export const BACKFILL_TERMINATION_DIALOG_BACKFILL_FRAGMENT = gql`
  fragment BackfillTerminationDialogBackfillFragment on PartitionBackfill {
    id
    status
    isAssetBackfill
  }
`;

export const BACKFILL_STEP_STATUS_DIALOG_BACKFILL_FRAGMENT = gql`
  fragment BackfillStepStatusDialogBackfillFragment on PartitionBackfill {
    id
    partitionNames
    partitionSet {
      id
      mode
      name
      pipelineName
      repositoryOrigin {
        id
        repositoryName
        repositoryLocationName
      }
    }
  }
`;

export const BACKFILL_ACTIONS_BACKFILL_FRAGMENT = gql`
  fragment BackfillActionsBackfillFragment on PartitionBackfill {
    id
    hasCancelPermission
    hasResumePermission
    isAssetBackfill
    status

    ...BackfillStepStatusDialogBackfillFragment
    ...BackfillTerminationDialogBackfillFragment
  }

  ${BACKFILL_STEP_STATUS_DIALOG_BACKFILL_FRAGMENT}
  ${BACKFILL_TERMINATION_DIALOG_BACKFILL_FRAGMENT}
`;
