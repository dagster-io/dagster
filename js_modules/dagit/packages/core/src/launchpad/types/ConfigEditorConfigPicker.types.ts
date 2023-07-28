// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ConfigPartitionsQueryVariables = Types.Exact<{
  repositorySelector: Types.RepositorySelector;
  partitionSetName: Types.Scalars['String'];
  assetKeys?: Types.InputMaybe<Array<Types.AssetKeyInput> | Types.AssetKeyInput>;
}>;

export type ConfigPartitionsQuery = {
  __typename: 'Query';
  partitionSetOrError:
    | {
        __typename: 'PartitionSet';
        id: string;
        partitionsOrError:
          | {__typename: 'Partitions'; results: Array<{__typename: 'Partition'; name: string}>}
          | {
              __typename: 'PythonError';
              message: string;
              stack: Array<string>;
              errorChain: Array<{
                __typename: 'ErrorChainLink';
                isExplicitLink: boolean;
                error: {__typename: 'PythonError'; message: string; stack: Array<string>};
              }>;
            };
      }
    | {__typename: 'PartitionSetNotFoundError'}
    | {__typename: 'PythonError'};
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    partitionDefinition: {
      __typename: 'PartitionDefinition';
      name: string | null;
      type: Types.PartitionDefinitionType;
    } | null;
  }>;
};

export type ConfigPartitionResultFragment = {__typename: 'Partition'; name: string};

export type ConfigPartitionSelectionQueryVariables = Types.Exact<{
  repositorySelector: Types.RepositorySelector;
  partitionSetName: Types.Scalars['String'];
  partitionName: Types.Scalars['String'];
}>;

export type ConfigPartitionSelectionQuery = {
  __typename: 'Query';
  partitionSetOrError:
    | {
        __typename: 'PartitionSet';
        id: string;
        partition: {
          __typename: 'Partition';
          name: string;
          solidSelection: Array<string> | null;
          mode: string;
          runConfigOrError:
            | {__typename: 'PartitionRunConfig'; yaml: string}
            | {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              };
          tagsOrError:
            | {
                __typename: 'PartitionTags';
                results: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
              }
            | {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              };
        } | null;
      }
    | {__typename: 'PartitionSetNotFoundError'}
    | {__typename: 'PythonError'};
};

export type ConfigEditorGeneratorPipelineFragment = {
  __typename: 'Pipeline';
  id: string;
  isJob: boolean;
  name: string;
  presets: Array<{
    __typename: 'PipelinePreset';
    name: string;
    mode: string;
    solidSelection: Array<string> | null;
    runConfigYaml: string;
    tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
  }>;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
};

export type ConfigEditorPipelinePresetFragment = {
  __typename: 'PipelinePreset';
  name: string;
  mode: string;
  solidSelection: Array<string> | null;
  runConfigYaml: string;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
};

export type ConfigEditorGeneratorPartitionSetsFragment = {
  __typename: 'PartitionSets';
  results: Array<{
    __typename: 'PartitionSet';
    id: string;
    name: string;
    mode: string;
    solidSelection: Array<string> | null;
  }>;
};

export type PartitionSetForConfigEditorFragment = {
  __typename: 'PartitionSet';
  id: string;
  name: string;
  mode: string;
  solidSelection: Array<string> | null;
};
