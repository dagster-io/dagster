import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';

const REPOSITORY_GRAPHS_FRAGMENT = gql`
  fragment RepositoryGraphsFragment on Repository {
    id
    usedSolids {
      definition {
        ... on CompositeSolidDefinition {
          id
          name
          description
        }
      }
      invocations {
        pipeline {
          id
          name
        }
        solidHandle {
          handleID
        }
      }
    }
    pipelines {
      id
      name
      isJob
      graphName
    }
  }
`;

export const WORSKPACE_GRAPHS_QUERY = gql`
  query WorkspaceGraphsQuery($selector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $selector) {
      ... on Repository {
        id
        ...RepositoryGraphsFragment
      }
      ...PythonErrorFragment
    }
  }

  ${REPOSITORY_GRAPHS_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
