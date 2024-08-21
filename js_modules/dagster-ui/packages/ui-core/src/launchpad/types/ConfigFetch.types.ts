// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ConfigPartitionForAssetJobQueryVariables = Types.Exact<{
  repositoryName: Types.Scalars['String']['input'];
  repositoryLocationName: Types.Scalars['String']['input'];
  jobName: Types.Scalars['String']['input'];
  partitionName: Types.Scalars['String']['input'];
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

export type ConfigPartitionSelectionQueryVariables = Types.Exact<{
  repositorySelector: Types.RepositorySelector;
  partitionSetName: Types.Scalars['String']['input'];
  partitionName: Types.Scalars['String']['input'];
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
