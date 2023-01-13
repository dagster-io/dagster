// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PartitionsBackfillSelectorQueryVariables = Types.Exact<{
  partitionSetName: Types.Scalars['String'];
  repositorySelector: Types.RepositorySelector;
  pipelineSelector: Types.PipelineSelector;
}>;

export type PartitionsBackfillSelectorQuery = {
  __typename: 'DagitQuery';
  partitionSetOrError:
    | {
        __typename: 'PartitionSet';
        id: string;
        name: string;
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
    | {__typename: 'PartitionSetNotFoundError'; message: string}
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
  pipelineSnapshotOrError:
    | {__typename: 'PipelineNotFoundError'; message: string}
    | {
        __typename: 'PipelineSnapshot';
        id: string;
        name: string;
        solidHandles: Array<{
          __typename: 'SolidHandle';
          handleID: string;
          solid: {
            __typename: 'Solid';
            name: string;
            definition:
              | {__typename: 'CompositeSolidDefinition'; name: string}
              | {__typename: 'SolidDefinition'; name: string};
            inputs: Array<{
              __typename: 'Input';
              dependsOn: Array<{__typename: 'Output'; solid: {__typename: 'Solid'; name: string}}>;
            }>;
            outputs: Array<{
              __typename: 'Output';
              dependedBy: Array<{__typename: 'Input'; solid: {__typename: 'Solid'; name: string}}>;
            }>;
          };
        }>;
      }
    | {__typename: 'PipelineSnapshotNotFoundError'; message: string}
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
  instance: {
    __typename: 'Instance';
    runQueuingSupported: boolean;
    runLauncher: {__typename: 'RunLauncher'; name: string} | null;
    daemonHealth: {
      __typename: 'DaemonHealth';
      id: string;
      daemonStatus: {__typename: 'DaemonStatus'; id: string; healthy: boolean | null};
    };
  };
};

export type PartitionStatusQueryVariables = Types.Exact<{
  partitionSetName: Types.Scalars['String'];
  repositorySelector: Types.RepositorySelector;
}>;

export type PartitionStatusQuery = {
  __typename: 'DagitQuery';
  partitionSetOrError:
    | {
        __typename: 'PartitionSet';
        id: string;
        name: string;
        partitionStatusesOrError:
          | {
              __typename: 'PartitionStatuses';
              results: Array<{
                __typename: 'PartitionStatus';
                id: string;
                partitionName: string;
                runStatus: Types.RunStatus | null;
              }>;
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
      }
    | {__typename: 'PartitionSetNotFoundError'; message: string}
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
};
