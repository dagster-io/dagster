// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type BackfillStatusesByAssetQueryVariables = Types.Exact<{
  backfillId: Types.Scalars['String'];
}>;

export type BackfillStatusesByAssetQuery = {
  __typename: 'DagitQuery';
  partitionBackfillOrError:
    | {
        __typename: 'PartitionBackfill';
        status: Types.BulkActionStatus;
        timestamp: number;
        endTimestamp: number | null;
        numPartitions: number | null;
        partitionSet: {
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
        } | null;
        partitionStatuses: {
          __typename: 'PartitionStatuses';
          results: Array<{
            __typename: 'PartitionStatus';
            id: string;
            partitionName: string;
            runStatus: Types.RunStatus | null;
            runDuration: number | null;
          }>;
        };
        assetPartitionsStatusCounts: Array<{
          __typename: 'AssetPartitionsStatusCounts';
          numPartitionsTargeted: number;
          numPartitionsRequested: number;
          numPartitionsCompleted: number;
          numPartitionsFailed: number;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
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

export type PartitionBackfillFragment = {
  __typename: 'PartitionBackfill';
  status: Types.BulkActionStatus;
  timestamp: number;
  endTimestamp: number | null;
  numPartitions: number | null;
  partitionSet: {
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
  } | null;
  partitionStatuses: {
    __typename: 'PartitionStatuses';
    results: Array<{
      __typename: 'PartitionStatus';
      id: string;
      partitionName: string;
      runStatus: Types.RunStatus | null;
      runDuration: number | null;
    }>;
  };
  assetPartitionsStatusCounts: Array<{
    __typename: 'AssetPartitionsStatusCounts';
    numPartitionsTargeted: number;
    numPartitionsRequested: number;
    numPartitionsCompleted: number;
    numPartitionsFailed: number;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
  }>;
};
