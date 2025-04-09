import {gql} from '../apollo-client';

export const CODE_LOCATION_DOCS_QUERY = gql`
  query CodeLocationDocsQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        locationDocsJsonOrError {
          ... on LocationDocsJson {
            json
          }
          ... on PythonError {
            message
          }
        }
      }
    }
  }
`;
