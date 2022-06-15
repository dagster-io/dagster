import {gql} from '@apollo/client';

export const CONFIG_EDITOR_RUN_CONFIG_SCHEMA_FRAGMENT = gql`
  fragment ConfigEditorRunConfigSchemaFragment on RunConfigSchema {
    rootConfigType {
      key
    }
    allConfigTypes {
      __typename
      key
      description
      isSelector
      typeParamKeys
      ... on RegularConfigType {
        givenName
      }
      ... on MapConfigType {
        keyLabelName
      }
      ... on EnumConfigType {
        givenName
        values {
          value
          description
        }
      }
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
        key
        scalarTypeKey
        nonScalarTypeKey
      }
    }
  }
`;
