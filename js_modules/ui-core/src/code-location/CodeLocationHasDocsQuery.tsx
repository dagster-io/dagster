import {gql} from '../apollo-client';

export const CODE_LOCATION_HAS_DOCS_QUERY = gql`
  query CodeLocationHasDocsQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        hasLocationDocs
      }
    }
  }
`;
