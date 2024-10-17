import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';

export const AUTOMATION_ASSET_SELECTION_FRAGMENT = gql`
  fragment AutomationAssetSelectionFragment on AssetSelection {
    assetSelectionString
    assetsOrError {
      ... on AssetConnection {
        nodes {
          id
          ...AssetSelectionNodeFragment
        }
      }
      ... on PythonError {
        ...PythonErrorFragment
      }
    }
  }

  fragment AssetSelectionNodeFragment on Asset {
    id
    key {
      path
    }
    definition {
      id
      automationCondition {
        __typename
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
