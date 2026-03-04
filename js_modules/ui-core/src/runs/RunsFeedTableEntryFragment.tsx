import {gql} from '../apollo-client';
import {RUN_ACTIONS_MENU_RUN_FRAGMENT} from './RunActionsMenuRunFragment';
import {
  BACKFILL_STEP_STATUS_DIALOG_BACKFILL_FRAGMENT,
  PARTITION_SET_FOR_BACKFILL_TABLE_FRAGMENT,
} from '../instance/backfill/BackfillFragments';

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
      numPartitions
      ...BackfillStepStatusDialogBackfillFragment
    }
  }

  ${PARTITION_SET_FOR_BACKFILL_TABLE_FRAGMENT}
  ${BACKFILL_STEP_STATUS_DIALOG_BACKFILL_FRAGMENT}
  ${RUN_ACTIONS_MENU_RUN_FRAGMENT}
`;
