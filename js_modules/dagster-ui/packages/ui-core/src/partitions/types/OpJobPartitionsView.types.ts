// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PartitionsStatusQueryVariables = Types.Exact<{
  partitionSetName: Types.Scalars['String']['input'];
  repositorySelector: Types.RepositorySelector;
}>;

export type PartitionsStatusQuery = {
  __typename: 'Query';
  partitionSetOrError:
    | {
        __typename: 'PartitionSet';
        id: string;
        name: string;
        pipelineName: string;
        hasLaunchBackfillPermission: boolean;
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
        partitionStatusesOrError:
          | {
              __typename: 'PartitionStatuses';
              results: Array<{
                __typename: 'PartitionStatus';
                id: string;
                partitionName: string;
                runStatus: Types.RunStatus | null;
                runDuration: number | null;
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

export type OpJobPartitionSetFragment = {
  __typename: 'PartitionSet';
  id: string;
  name: string;
  pipelineName: string;
  hasLaunchBackfillPermission: boolean;
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
  partitionStatusesOrError:
    | {
        __typename: 'PartitionStatuses';
        results: Array<{
          __typename: 'PartitionStatus';
          id: string;
          partitionName: string;
          runStatus: Types.RunStatus | null;
          runDuration: number | null;
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
};

export type OpJobPartitionStatusFragment = {
  __typename: 'PartitionStatus';
  id: string;
  partitionName: string;
  runStatus: Types.RunStatus | null;
  runDuration: number | null;
};

export const PartitionsStatusQueryVersion = '1dc21ab131710de7e132d2da3aea58eb2ba640344eeae0c744b94a6558b50ed6';
