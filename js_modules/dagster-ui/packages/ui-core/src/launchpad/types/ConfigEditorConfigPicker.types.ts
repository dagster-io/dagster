// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ConfigPartitionsQueryVariables = Types.Exact<{
  repositorySelector: Types.RepositorySelector;
  partitionSetName: Types.Scalars['String']['input'];
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
};

export type ConfigPartitionResultFragment = {__typename: 'Partition'; name: string};

export type ConfigPartitionsAssetsQueryVariables = Types.Exact<{
  params: Types.PipelineSelector;
  assetKeys?: Types.InputMaybe<Array<Types.AssetKeyInput> | Types.AssetKeyInput>;
}>;

export type ConfigPartitionsAssetsQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'; message: string}
    | {
        __typename: 'Pipeline';
        id: string;
        partitionKeysOrError: {__typename: 'PartitionKeys'; partitionKeys: Array<string>};
      }
    | {__typename: 'PipelineNotFoundError'; message: string}
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

export const ConfigPartitionsQueryVersion = 'b2982b87aa317ad4df2f4227ac4285280de352fa571e952f56f9f85e2a0096fc';

export const ConfigPartitionsAssetsQueryVersion = '02438f2590d14870b0df3107680c2d33da2c7a492a3f8a507c591f7ad4555409';
