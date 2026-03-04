import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {ASSET_TABLE_DEFINITION_FRAGMENT} from '../assets/AssetTableFragment';

export const REPO_ASSET_TABLE_FRAGMENT = gql`
  fragment RepoAssetTableFragment on AssetNode {
    id
    assetKey {
      path
    }
    groupName
    ...AssetTableDefinitionFragment
  }

  ${ASSET_TABLE_DEFINITION_FRAGMENT}
`;

export const WORKSPACE_ASSETS_QUERY = gql`
  query WorkspaceAssetsQuery($selector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $selector) {
      ... on Repository {
        id
        name
        assetNodes {
          id
          ...RepoAssetTableFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${REPO_ASSET_TABLE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
