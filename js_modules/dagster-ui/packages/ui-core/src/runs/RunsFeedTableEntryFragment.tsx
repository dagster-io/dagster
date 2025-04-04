import {RUN_ACTIONS_MENU_RUN_FRAGMENT} from './RunActionsMenu';
import {gql} from '../apollo-client';
import {BACKFILL_TARGET_FRAGMENT} from './BackfillTarget';
import {BACKFILL_STEP_STATUS_DIALOG_BACKFILL_FRAGMENT} from '../instance/backfill/BackfillFragments';

export const RUNS_FEED_TABLE_ENTRY_FRAGMENT = gql`
  fragment RunsFeedTableEntryFragment on RunsFeedEntry {
    __typename
    id
    runStatus
    creationTime
    startTime
    endTime
    tags {
      key
      value
    }
    jobName
    assetSelection {
      ... on AssetKey {
        path
      }
    }
    assetCheckSelection {
      name
      assetKey {
        path
      }
    }
    ... on Run {
      repositoryOrigin {
        id
        repositoryLocationName
        repositoryName
      }
      ...RunActionsMenuRunFragment
    }
    ... on PartitionBackfill {
      backfillStatus: status
      partitionSetName
      partitionSet {
        id
      }
      assetSelection {
        path
      }

      hasCancelPermission
      hasResumePermission
      isAssetBackfill
      numPartitions
      isAssetBackfill

      ...BackfillStepStatusDialogBackfillFragment
      ...BackfillTargetFragment
    }
  }

  ${RUN_ACTIONS_MENU_RUN_FRAGMENT}
  ${BACKFILL_STEP_STATUS_DIALOG_BACKFILL_FRAGMENT}
  ${BACKFILL_TARGET_FRAGMENT}
`;
