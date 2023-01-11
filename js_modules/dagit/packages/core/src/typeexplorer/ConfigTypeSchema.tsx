import {ConfigSchema} from '@dagster-io/ui';

import {graphql} from '../graphql';

export type {ConfigSchema as ConfigTypeSchema};

export const CONFIG_TYPE_SCHEMA_FRAGMENT = graphql(`
  fragment ConfigTypeSchemaFragment on ConfigType {
    __typename
    ... on EnumConfigType {
      givenName
      values {
        value
        description
      }
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
`);
