/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetKeyInput = {
  path: Array<string>;
};

export type RepositorySelector = {
  repositoryLocationName: string;
  repositoryName: string;
};

export type ConfigPartitionForAssetJobQueryVariables = Exact<{
  repositoryName: string;
  repositoryLocationName: string;
  jobName: string;
  partitionName: string;
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type ConfigPartitionForAssetJobQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'}
    | {
        __typename: 'Pipeline';
        id: string;
        partition: {
          __typename: 'PartitionTagsAndConfig';
          name: string;
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
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PythonError'};
};

export type ConfigPartitionSelectionQueryVariables = Exact<{
  repositorySelector: Types.RepositorySelector;
  partitionSetName: string;
  partitionName: string;
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

export const ConfigPartitionForAssetJobQueryVersion = '367eaeeb62b9e2339ab6c07a1e315310fd1a095b7ba7c8fa7a1e51282ca84796';

export const ConfigPartitionSelectionQueryVersion = '54bfeba0e497a1ee185cf7d7fa251ce81cffdf97a3f234b5022f3c619e29ebd5';
