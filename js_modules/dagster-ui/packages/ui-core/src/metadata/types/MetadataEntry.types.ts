// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type MetadataEntryFragment_AssetMetadataEntry_ = {
  __typename: 'AssetMetadataEntry';
  label: string;
  description: string | null;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
};

export type MetadataEntryFragment_BoolMetadataEntry_ = {
  __typename: 'BoolMetadataEntry';
  boolValue: boolean | null;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_FloatMetadataEntry_ = {
  __typename: 'FloatMetadataEntry';
  floatValue: number | null;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_IntMetadataEntry_ = {
  __typename: 'IntMetadataEntry';
  intValue: number | null;
  intRepr: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_JsonMetadataEntry_ = {
  __typename: 'JsonMetadataEntry';
  jsonString: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_MarkdownMetadataEntry_ = {
  __typename: 'MarkdownMetadataEntry';
  mdStr: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_NotebookMetadataEntry_ = {
  __typename: 'NotebookMetadataEntry';
  path: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_NullMetadataEntry_ = {
  __typename: 'NullMetadataEntry';
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_PathMetadataEntry_ = {
  __typename: 'PathMetadataEntry';
  path: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_PipelineRunMetadataEntry_ = {
  __typename: 'PipelineRunMetadataEntry';
  runId: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_PythonArtifactMetadataEntry_ = {
  __typename: 'PythonArtifactMetadataEntry';
  module: string;
  name: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_TableMetadataEntry_ = {
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

export type MetadataEntryFragment_TableSchemaMetadataEntry_ = {
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

export type MetadataEntryFragment_TextMetadataEntry_ = {
  __typename: 'TextMetadataEntry';
  text: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment_UrlMetadataEntry_ = {
  __typename: 'UrlMetadataEntry';
  url: string;
  label: string;
  description: string | null;
};

export type MetadataEntryFragment =
  | MetadataEntryFragment_AssetMetadataEntry_
  | MetadataEntryFragment_BoolMetadataEntry_
  | MetadataEntryFragment_FloatMetadataEntry_
  | MetadataEntryFragment_IntMetadataEntry_
  | MetadataEntryFragment_JsonMetadataEntry_
  | MetadataEntryFragment_MarkdownMetadataEntry_
  | MetadataEntryFragment_NotebookMetadataEntry_
  | MetadataEntryFragment_NullMetadataEntry_
  | MetadataEntryFragment_PathMetadataEntry_
  | MetadataEntryFragment_PipelineRunMetadataEntry_
  | MetadataEntryFragment_PythonArtifactMetadataEntry_
  | MetadataEntryFragment_TableMetadataEntry_
  | MetadataEntryFragment_TableSchemaMetadataEntry_
  | MetadataEntryFragment_TextMetadataEntry_
  | MetadataEntryFragment_UrlMetadataEntry_;

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
