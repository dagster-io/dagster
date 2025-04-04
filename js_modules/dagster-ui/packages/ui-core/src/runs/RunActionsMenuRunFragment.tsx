import {gql} from '../apollo-client';

export const RUN_ACTIONS_MENU_RUN_FRAGMENT = gql`
  fragment RunActionsMenuRunFragment on Run {
    id
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
    tags {
      key
      value
    }
    hasReExecutePermission
    hasTerminatePermission
    hasDeletePermission
    canTerminate
    mode
    status
    pipelineName
    pipelineSnapshotId
    repositoryOrigin {
      repositoryName
      repositoryLocationName
    }
    hasRunMetricsEnabled
  }
`;
