import {gql} from '../apollo-client';

export const RUN_TAG_KEYS_QUERY = gql`
  query RunTagKeysQuery {
    runTagKeysOrError {
      ... on RunTagKeys {
        keys
      }
    }
  }
`;

export const RUN_TAG_VALUES_QUERY = gql`
  query RunTagValuesQuery($tagKeys: [String!]!) {
    runTagsOrError(tagKeys: $tagKeys) {
      ... on RunTags {
        tags {
          key
          values
        }
      }
    }
  }
`;
