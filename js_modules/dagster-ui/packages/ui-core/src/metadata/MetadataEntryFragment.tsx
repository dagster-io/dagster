import {TABLE_SCHEMA_FRAGMENT} from './TableSchemaFragment';
import {gql} from '../apollo-client';

export const METADATA_ENTRY_FRAGMENT = gql`
  fragment MetadataEntryFragment on MetadataEntry {
    label
    description
    ... on PathMetadataEntry {
      path
    }
    ... on NotebookMetadataEntry {
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
    ... on TimestampMetadataEntry {
      timestamp
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
    ... on JobMetadataEntry {
      jobName
      repositoryName
      locationName
    }
    ... on TableColumnLineageMetadataEntry {
      lineage {
        columnName
        columnDeps {
          assetKey {
            path
          }
          columnName
        }
      }
    }
    ... on TableMetadataEntry {
      ...TableMetadataEntryFragment
    }
    ... on TableSchemaMetadataEntry {
      ...TableSchemaForMetadataEntry
    }
    ... on CodeReferencesMetadataEntry {
      codeReferences {
        __typename
        ... on LocalFileCodeReference {
          filePath
          lineNumber
          label
        }
        ... on UrlCodeReference {
          url
          label
        }
      }
    }
  }

  fragment TableMetadataEntryFragment on TableMetadataEntry {
    label
    table {
      records
      schema {
        ...TableSchemaFragment
      }
    }
  }

  fragment TableSchemaForMetadataEntry on TableSchemaMetadataEntry {
    schema {
      ...TableSchemaFragment
    }
  }

  ${TABLE_SCHEMA_FRAGMENT}
`;
