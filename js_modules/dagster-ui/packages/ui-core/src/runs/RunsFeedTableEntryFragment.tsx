import {RUN_ACTIONS_MENU_RUN_FRAGMENT} from './RunActionsMenu';
import {gql} from '../apollo-client';
import {BACKFILL_TABLE_FRAGMENT_FOR_STEP_STATUS_DIALOG} from '../instance/backfill/BackfillFragments';
import {PARTITION_SET_FOR_BACKFILL_TABLE_FRAGMENT} from '../instance/backfill/BackfillTable';

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
        ...PartitionSetForBackfillTableFragment
      }
      assetSelection {
        path
      }

      hasCancelPermission
      hasResumePermission
      isAssetBackfill
      numCancelable
      numPartitions
      ...BackfillTableFragmentForStepStatusDialog
    }
  }

  ${RUN_ACTIONS_MENU_RUN_FRAGMENT}
  ${PARTITION_SET_FOR_BACKFILL_TABLE_FRAGMENT}
  ${BACKFILL_TABLE_FRAGMENT_FOR_STEP_STATUS_DIALOG}
`;
