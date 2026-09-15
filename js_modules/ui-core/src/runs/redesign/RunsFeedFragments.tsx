import {gql} from '../../apollo-client';

export const RUN_SUMMARY_FRAGMENT = gql`
  fragment RunSummaryFragment on Run {
    id
    runId
    runStatus
    creationTime
    startTime
    endTime
    jobName
    mode
    pipelineSnapshotId
    repositoryOrigin {
      id
      repositoryName
      repositoryLocationName
    }
    tags {
      key
      value
    }
    parentRunId
    rootRunId
    assetSelectionPreview: assetSelection(limit: 25) {
      path
    }
    assetSelectionCount
    assetCheckSelectionPreview: assetCheckSelection(limit: 25) {
      assetKey {
        path
      }
      name
    }
    assetCheckSelectionCount
    hasReExecutePermission
    hasTerminatePermission
    hasDeletePermission
    canTerminate
    hasRunMetricsEnabled
  }
`;

export const BACKFILL_SUMMARY_FRAGMENT = gql`
  fragment BackfillSummaryFragment on PartitionBackfill {
    id
    backfillStatus: status
    runStatus
    creationTime
    startTime
    endTime
    backfillJobName: jobName
    partitionSetName
    isAssetBackfill
    title
    user
    tags {
      key
      value
    }
    hasCancelPermission
    hasResumePermission
  }
`;

export const RUNS_FEED_ENTRY_FRAGMENT = gql`
  fragment RunsFeedEntryFragment on RunsFeedEntry {
    __typename
    ... on Run {
      ...RunSummaryFragment
    }
    ... on PartitionBackfill {
      ...BackfillSummaryFragment
    }
  }

  ${RUN_SUMMARY_FRAGMENT}
  ${BACKFILL_SUMMARY_FRAGMENT}
`;

export const RUN_SELECTION_DETAILS_FRAGMENT = gql`
  fragment RunSelectionDetailsFragment on Run {
    id
    runId
    assetSelection {
      path
    }
    assetCheckSelection {
      assetKey {
        path
      }
      name
    }
    executionPlan {
      assetKeys {
        path
      }
      steps {
        key
      }
    }
  }
`;
