// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetColumnLineageQueryVariables = Types.Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type AssetColumnLineageQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    metadataEntries: Array<
      | {__typename: 'AssetMetadataEntry'; label: string}
      | {__typename: 'BoolMetadataEntry'; label: string}
      | {__typename: 'CodeReferencesMetadataEntry'; label: string}
      | {__typename: 'FloatMetadataEntry'; label: string}
      | {__typename: 'IntMetadataEntry'; label: string}
      | {__typename: 'JobMetadataEntry'; label: string}
      | {__typename: 'JsonMetadataEntry'; label: string}
      | {__typename: 'MarkdownMetadataEntry'; label: string}
      | {__typename: 'NotebookMetadataEntry'; label: string}
      | {__typename: 'NullMetadataEntry'; label: string}
      | {__typename: 'PathMetadataEntry'; label: string}
      | {__typename: 'PipelineRunMetadataEntry'; label: string}
      | {__typename: 'PythonArtifactMetadataEntry'; label: string}
      | {
          __typename: 'TableColumnLineageMetadataEntry';
          label: string;
          lineage: Array<{
            __typename: 'TableColumnLineageEntry';
            columnName: string;
            columnDeps: Array<{
              __typename: 'TableColumnDep';
              columnName: string;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }>;
          }>;
        }
      | {__typename: 'TableMetadataEntry'; label: string}
      | {
          __typename: 'TableSchemaMetadataEntry';
          label: string;
          schema: {
            __typename: 'TableSchema';
            columns: Array<{
              __typename: 'TableColumn';
              name: string;
              type: string;
              description: string | null;
              tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
            }>;
          };
        }
      | {__typename: 'TextMetadataEntry'; label: string}
      | {__typename: 'TimestampMetadataEntry'; label: string}
      | {__typename: 'UrlMetadataEntry'; label: string}
    >;
    assetMaterializations: Array<{
      __typename: 'MaterializationEvent';
      timestamp: string;
      metadataEntries: Array<
        | {__typename: 'AssetMetadataEntry'; label: string}
        | {__typename: 'BoolMetadataEntry'; label: string}
        | {__typename: 'CodeReferencesMetadataEntry'; label: string}
        | {__typename: 'FloatMetadataEntry'; label: string}
        | {__typename: 'IntMetadataEntry'; label: string}
        | {__typename: 'JobMetadataEntry'; label: string}
        | {__typename: 'JsonMetadataEntry'; label: string}
        | {__typename: 'MarkdownMetadataEntry'; label: string}
        | {__typename: 'NotebookMetadataEntry'; label: string}
        | {__typename: 'NullMetadataEntry'; label: string}
        | {__typename: 'PathMetadataEntry'; label: string}
        | {__typename: 'PipelineRunMetadataEntry'; label: string}
        | {__typename: 'PythonArtifactMetadataEntry'; label: string}
        | {
            __typename: 'TableColumnLineageMetadataEntry';
            label: string;
            lineage: Array<{
              __typename: 'TableColumnLineageEntry';
              columnName: string;
              columnDeps: Array<{
                __typename: 'TableColumnDep';
                columnName: string;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }>;
            }>;
          }
        | {__typename: 'TableMetadataEntry'; label: string}
        | {
            __typename: 'TableSchemaMetadataEntry';
            label: string;
            schema: {
              __typename: 'TableSchema';
              columns: Array<{
                __typename: 'TableColumn';
                name: string;
                type: string;
                description: string | null;
                tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
              }>;
            };
          }
        | {__typename: 'TextMetadataEntry'; label: string}
        | {__typename: 'TimestampMetadataEntry'; label: string}
        | {__typename: 'UrlMetadataEntry'; label: string}
      >;
    }>;
  }>;
};

export const AssetColumnLineageVersion = 'ce1683cb51cf7ac96c82f05bbf5f1cc2df57ce6c944615109e30dc6d93246dc4';
