import {RUN_TAGS_FRAGMENT} from './RunTagsFragment';
import {RUN_TIME_FRAGMENT} from './RunUtils';
import {gql} from '../apollo-client';

export const RUN_TABLE_RUN_FRAGMENT = gql`
  fragment RunTableRunFragment on Run {
    id
    status
    stepKeysToExecute
    canTerminate
    hasReExecutePermission
    hasTerminatePermission
    hasDeletePermission
    hasRunMetricsEnabled
    mode
    rootRunId
    parentRunId
    pipelineSnapshotId
    pipelineName
    repositoryOrigin {
      id
      repositoryName
      repositoryLocationName
    }
    solidSelection
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
    status
    tags {
      ...RunTagsFragment
    }
    ...RunTimeFragment
  }

  ${RUN_TIME_FRAGMENT}
  ${RUN_TAGS_FRAGMENT}
`;
