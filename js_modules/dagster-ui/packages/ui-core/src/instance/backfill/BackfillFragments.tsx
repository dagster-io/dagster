import {gql} from '../../apollo-client';

export const BACKFILL_TERMINATION_DIALOG_BACKFILL_FRAGMENT = gql`
  fragment BackfillTerminationDialogBackfillFragment on PartitionBackfill {
    id
    status
    isAssetBackfill
    numCancelable
  }
`;

// this is the cheap version of the fragment that determines whether we should even show the step status dialog
export const BACKFILL_TABLE_FRAGMENT_FOR_STEP_STATUS_DIALOG = gql`
  fragment BackfillTableFragmentForStepStatusDialog on PartitionBackfill {
    id
    partitionSet {
      id
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
    numCancelable

    ...BackfillTableFragmentForStepStatusDialog
    ...BackfillTerminationDialogBackfillFragment
  }

  ${BACKFILL_TABLE_FRAGMENT_FOR_STEP_STATUS_DIALOG}
  ${BACKFILL_TERMINATION_DIALOG_BACKFILL_FRAGMENT}
`;
