import {RUN_ASSET_SELECTION_FRAGMENT} from './RunsFeedFragments';
import {gql} from '../../apollo-client';

export const RUN_ACTIONS_MENU_DETAILS_FRAGMENT = gql`
  fragment RunActionsMenuDetailsFragment on Run {
    id
    parentPipelineSnapshotId
    runConfigYaml
    ...RunAssetSelectionFragment
  }

  ${RUN_ASSET_SELECTION_FRAGMENT}
`;

export const RUN_ACTIONS_MENU_QUERY = gql`
  query RunActionsMenuQuery($runId: ID!) {
    runOrError(runId: $runId) {
      ... on Run {
        id
        ...RunActionsMenuDetailsFragment
      }
    }
  }

  ${RUN_ACTIONS_MENU_DETAILS_FRAGMENT}
`;
