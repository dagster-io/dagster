import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';

export const RESOURCE_ENTRY_FRAGMENT = gql`
  fragment ResourceEntryFragment on ResourceDetails {
    name
    description
    resourceType
    parentResources {
      name
    }
    assetKeysUsing {
      path
    }
    jobsOpsUsing {
      jobName
    }
    schedulesUsing
    sensorsUsing
  }
`;

export const WORKSPACE_RESOURCES_QUERY = gql`
  query WorkspaceResourcesQuery($selector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $selector) {
      ... on Repository {
        id
        name
        allTopLevelResourceDetails {
          id
          ...ResourceEntryFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${RESOURCE_ENTRY_FRAGMENT}
`;
