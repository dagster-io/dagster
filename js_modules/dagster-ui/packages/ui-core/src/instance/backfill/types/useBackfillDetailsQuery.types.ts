// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type JobBackfillDetailsFragment = {
  __typename: 'PartitionStatuses';
  results: Array<{
    __typename: 'PartitionStatus';
    id: string;
    partitionName: string;
    runId: string | null;
    runStatus: Types.RunStatus | null;
    runDuration: number | null;
  }>;
};

export type AssetBackfillDetailsFragment = {
  __typename: 'AssetBackfillData';
  rootTargetedPartitions: {
    __typename: 'AssetBackfillTargetPartitions';
    partitionKeys: Array<string> | null;
    ranges: Array<{__typename: 'PartitionKeyRange'; start: string; end: string}> | null;
  } | null;
  assetBackfillStatuses: Array<
    | {
        __typename: 'AssetPartitionsStatusCounts';
        numPartitionsTargeted: number;
        numPartitionsInProgress: number;
        numPartitionsMaterialized: number;
        numPartitionsFailed: number;
        assetKey: {__typename: 'AssetKey'; path: Array<string>};
      }
    | {
        __typename: 'UnpartitionedAssetStatus';
        inProgress: boolean;
        materialized: boolean;
        failed: boolean;
        assetKey: {__typename: 'AssetKey'; path: Array<string>};
      }
  >;
};

export type BackfillDetailsQueryVariables = Types.Exact<{
  backfillId: Types.Scalars['String']['input'];
}>;

export type BackfillDetailsQuery = {
  __typename: 'Query';
  partitionBackfillOrError:
    | {__typename: 'BackfillNotFoundError'; message: string}
    | {
        __typename: 'PartitionBackfill';
        id: string;
        status: Types.BulkActionStatus;
        timestamp: number;
        endTimestamp: number | null;
        numPartitions: number | null;
        isAssetBackfill: boolean;
        partitionSetName: string | null;
        hasCancelPermission: boolean;
        hasResumePermission: boolean;
        numCancelable: number;
        partitionNames: Array<string> | null;
        assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        } | null;
        assetBackfillData: {
          __typename: 'AssetBackfillData';
          rootTargetedPartitions: {
            __typename: 'AssetBackfillTargetPartitions';
            partitionKeys: Array<string> | null;
            ranges: Array<{__typename: 'PartitionKeyRange'; start: string; end: string}> | null;
          } | null;
          assetBackfillStatuses: Array<
            | {
                __typename: 'AssetPartitionsStatusCounts';
                numPartitionsTargeted: number;
                numPartitionsInProgress: number;
                numPartitionsMaterialized: number;
                numPartitionsFailed: number;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }
            | {
                __typename: 'UnpartitionedAssetStatus';
                inProgress: boolean;
                materialized: boolean;
                failed: boolean;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }
          >;
        } | null;
        partitionStatuses: {
          __typename: 'PartitionStatuses';
          results: Array<{
            __typename: 'PartitionStatus';
            id: string;
            partitionName: string;
            runId: string | null;
            runStatus: Types.RunStatus | null;
            runDuration: number | null;
          }>;
        } | null;
        partitionSet: {
          __typename: 'PartitionSet';
          id: string;
          mode: string;
          name: string;
          pipelineName: string;
          repositoryOrigin: {
            __typename: 'RepositoryOrigin';
            id: string;
            repositoryName: string;
            repositoryLocationName: string;
          };
        } | null;
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

export type BackfillDetailsBackfillFragment = {
  __typename: 'PartitionBackfill';
  id: string;
  status: Types.BulkActionStatus;
  timestamp: number;
  endTimestamp: number | null;
  numPartitions: number | null;
  isAssetBackfill: boolean;
  partitionSetName: string | null;
  hasCancelPermission: boolean;
  hasResumePermission: boolean;
  numCancelable: number;
  partitionNames: Array<string> | null;
  assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
  error: {
    __typename: 'PythonError';
    message: string;
    stack: Array<string>;
    errorChain: Array<{
      __typename: 'ErrorChainLink';
      isExplicitLink: boolean;
      error: {__typename: 'PythonError'; message: string; stack: Array<string>};
    }>;
  } | null;
  assetBackfillData: {
    __typename: 'AssetBackfillData';
    rootTargetedPartitions: {
      __typename: 'AssetBackfillTargetPartitions';
      partitionKeys: Array<string> | null;
      ranges: Array<{__typename: 'PartitionKeyRange'; start: string; end: string}> | null;
    } | null;
    assetBackfillStatuses: Array<
      | {
          __typename: 'AssetPartitionsStatusCounts';
          numPartitionsTargeted: number;
          numPartitionsInProgress: number;
          numPartitionsMaterialized: number;
          numPartitionsFailed: number;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
        }
      | {
          __typename: 'UnpartitionedAssetStatus';
          inProgress: boolean;
          materialized: boolean;
          failed: boolean;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
        }
    >;
  } | null;
  partitionStatuses: {
    __typename: 'PartitionStatuses';
    results: Array<{
      __typename: 'PartitionStatus';
      id: string;
      partitionName: string;
      runId: string | null;
      runStatus: Types.RunStatus | null;
      runDuration: number | null;
    }>;
  } | null;
  partitionSet: {
    __typename: 'PartitionSet';
    id: string;
    mode: string;
    name: string;
    pipelineName: string;
    repositoryOrigin: {
      __typename: 'RepositoryOrigin';
      id: string;
      repositoryName: string;
      repositoryLocationName: string;
    };
  } | null;
};

export const BackfillDetailsQueryVersion = 'b2e50b372c779a994a7fdcdbef873890bf39716520774315b9e880ae59375217';
