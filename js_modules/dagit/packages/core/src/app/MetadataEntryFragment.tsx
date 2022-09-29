import {gql} from '@apollo/client';

import {TABLE_SCHEMA_FRAGMENT} from './TableSchemaFragment';

export const METADATA_ENTRY_FRAGMENT = gql`
  fragment MetadataEntryFragment on MetadataEntry {
    __typename
    label
    description
    ... on PathMetadataEntry {
      path
    }
    ... on JsonMetadataEntry {
      jsonString
    }
    ... on UrlMetadataEntry {
      url
    }
    ... on TextMetadataEntry {
      text
    }
    ... on MarkdownMetadataEntry {
      mdStr
    }
    ... on PythonArtifactMetadataEntry {
      module
      name
    }
    ... on FloatMetadataEntry {
      floatValue
    }
    ... on IntMetadataEntry {
      intValue
      intRepr
    }
    ... on BoolMetadataEntry {
      boolValue
    }
    ... on PipelineRunMetadataEntry {
      runId
    }
    ... on AssetMetadataEntry {
      assetKey {
        path
      }
    }
    ... on TableMetadataEntry {
      table {
        records
        schema {
          ...TableSchemaFragment
        }
      }
    }
    ... on TableSchemaMetadataEntry {
      schema {
        ...TableSchemaFragment
      }
    }
  }
  ${TABLE_SCHEMA_FRAGMENT}
`;
