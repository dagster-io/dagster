import {gql} from '../apollo-client';

export const CODE_LOCATION_PAGE_DOCS_QUERY = gql`
  query CodeLocationPageDocsQuery {
    repositoriesOrError {
      ... on RepositoryConnection {
        nodes {
          ... on Repository {
            id
            name
            location {
              name
              id
            }
            hasLocationDocs
          }
        }
      }
    }
  }
`;
