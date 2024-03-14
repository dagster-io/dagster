// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type MetadataEntryFragment_AssetMetadataEntry = {
  __typename: 'AssetMetadataEntry';
  label: string;
  description: string | null;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
};

export type MetadataEntryFragment_BoolMetadataEntry = {
  __typename: 'BoolMetadataEntry';
  boolValue: boolean | null;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_FloatMetadataEntry = {
  __typename: 'FloatMetadataEntry';
  floatValue: number | null;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_IntMetadataEntry = {
  __typename: 'IntMetadataEntry';
  intValue: number | null;
  intRepr: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_JobMetadataEntry = {
  __typename: 'JobMetadataEntry';
  jobName: string;
  repositoryName: string | null;
  locationName: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_JsonMetadataEntry = {
  __typename: 'JsonMetadataEntry';
  jsonString: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_MarkdownMetadataEntry = {
  __typename: 'MarkdownMetadataEntry';
  mdStr: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_NotebookMetadataEntry = {
  __typename: 'NotebookMetadataEntry';
  path: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_NullMetadataEntry = {
  __typename: 'NullMetadataEntry';
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_PathMetadataEntry = {
  __typename: 'PathMetadataEntry';
  path: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_PipelineRunMetadataEntry = {
  __typename: 'PipelineRunMetadataEntry';
  runId: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_PythonArtifactMetadataEntry = {
  __typename: 'PythonArtifactMetadataEntry';
  module: string;
  name: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_TableMetadataEntry = {
  __typename: 'TableMetadataEntry';
  label: string;
  description: string | null;
  table: {
    __typename: 'Table';
    records: Array<string>;
    schema: {
      __typename: 'TableSchema';
      columns: Array<{
        __typename: 'TableColumn';
        name: string;
        description: string | null;
        type: string;
        constraints: {
          __typename: 'TableColumnConstraints';
          nullable: boolean;
          unique: boolean;
          other: Array<string>;
        };
      }>;
      constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
    };
  };
};

export type MetadataEntryFragment_TableSchemaMetadataEntry = {
  __typename: 'TableSchemaMetadataEntry';
  label: string;
  description: string | null;
  schema: {
    __typename: 'TableSchema';
    columns: Array<{
      __typename: 'TableColumn';
      name: string;
      description: string | null;
      type: string;
      constraints: {
        __typename: 'TableColumnConstraints';
        nullable: boolean;
        unique: boolean;
        other: Array<string>;
      };
    }>;
    constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
  };
};

export type MetadataEntryFragment_TextMetadataEntry = {
  __typename: 'TextMetadataEntry';
  text: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_TimestampMetadataEntry = {
  __typename: 'TimestampMetadataEntry';
  timestamp: number | null;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_UrlMetadataEntry = {
  __typename: 'UrlMetadataEntry';
  url: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment =
  | MetadataEntryFragment_AssetMetadataEntry
  | MetadataEntryFragment_BoolMetadataEntry
  | MetadataEntryFragment_FloatMetadataEntry
  | MetadataEntryFragment_IntMetadataEntry
  | MetadataEntryFragment_JobMetadataEntry
  | MetadataEntryFragment_JsonMetadataEntry
  | MetadataEntryFragment_MarkdownMetadataEntry
  | MetadataEntryFragment_NotebookMetadataEntry
  | MetadataEntryFragment_NullMetadataEntry
  | MetadataEntryFragment_PathMetadataEntry
  | MetadataEntryFragment_PipelineRunMetadataEntry
  | MetadataEntryFragment_PythonArtifactMetadataEntry
  | MetadataEntryFragment_TableMetadataEntry
  | MetadataEntryFragment_TableSchemaMetadataEntry
  | MetadataEntryFragment_TextMetadataEntry
  | MetadataEntryFragment_TimestampMetadataEntry
  | MetadataEntryFragment_UrlMetadataEntry;

export type TableSchemaForMetadataEntryFragment = {
  __typename: 'TableSchemaMetadataEntry';
  schema: {
    __typename: 'TableSchema';
    columns: Array<{
      __typename: 'TableColumn';
      name: string;
      description: string | null;
      type: string;
      constraints: {
        __typename: 'TableColumnConstraints';
        nullable: boolean;
        unique: boolean;
        other: Array<string>;
      };
    }>;
    constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
  };
};
