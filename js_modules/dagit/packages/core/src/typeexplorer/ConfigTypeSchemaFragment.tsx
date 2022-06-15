import {gql} from '@apollo/client';

export const CONFIG_TYPE_SCHEMA_FRAGMENT = gql`
  fragment ConfigTypeSchemaFragment on ConfigType {
    __typename
    ... on EnumConfigType {
      givenName
    }
    ... on RegularConfigType {
      givenName
    }
    key
    description
    isSelector
    typeParamKeys
    ... on CompositeConfigType {
      fields {
        name
        description
        isRequired
        configTypeKey
        defaultValueAsJson
      }
    }
    ... on ScalarUnionConfigType {
      scalarTypeKey
      nonScalarTypeKey
    }
    ... on MapConfigType {
      keyLabelName
    }
  }
`;
