import {gql} from '@apollo/client';

export const TABLE_SCHEMA_FRAGMENT = gql`
  fragment TableSchemaFragment on TableSchema {
    __typename
    columns {
      name
      description
      type
      constraints {
        nullable
        unique
        other
      }
    }
    constraints {
      other
    }
  }
`;
