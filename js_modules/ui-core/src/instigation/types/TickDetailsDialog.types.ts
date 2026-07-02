/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DynamicPartitionsRequestType = 'ADD_PARTITIONS' | 'DELETE_PARTITIONS';

export type InstigationSelector = {
  name: string;
  repositoryLocationName: string;
  repositoryName: string;
};

export type InstigationTickStatus = 'FAILURE' | 'SKIPPED' | 'STARTED' | 'SUCCESS';

export type InstigationType = 'AUTO_MATERIALIZE' | 'SCHEDULE' | 'SENSOR';

export type RunStatus =
  | 'CANCELED'
  | 'CANCELING'
  | 'FAILURE'
  | 'MANAGED'
  | 'NOT_STARTED'
  | 'QUEUED'
  | 'STARTED'
  | 'STARTING'
  | 'SUCCESS';

export type SelectedTickQueryVariables = Exact<{
  instigationSelector: Types.InstigationSelector;
  tickId: string;
}>;

export type SelectedTickQuery = {
  __typename: 'Query';
  instigationStateOrError:
    | {
        __typename: 'InstigationState';
        id: string;
        tick: {
          __typename: 'InstigationTick';
          id: string;
          requestedAssetMaterializationCount: number;
          autoMaterializeAssetEvaluationId: string | null;
          tickId: string;
          status: Types.InstigationTickStatus;
          timestamp: number;
          endTimestamp: number | null;
          cursor: string | null;
          instigationType: Types.InstigationType;
          skipReason: string | null;
          runIds: Array<string>;
          originRunIds: Array<string>;
          logKey: Array<string> | null;
          runKeys: Array<string>;
          requestedAssetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
          requestedMaterializationsForAssets: Array<{
            __typename: 'RequestedMaterializationsForAsset';
            partitionKeys: Array<string>;
            assetKey: {__typename: 'AssetKey'; path: Array<string>};
          }>;
          runs: Array<{__typename: 'Run'; id: string; status: Types.RunStatus}>;
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
          dynamicPartitionsRequestResults: Array<{
            __typename: 'DynamicPartitionsRequestResult';
            partitionsDefName: string;
            partitionKeys: Array<string> | null;
            skippedPartitionKeys: Array<string>;
            type: Types.DynamicPartitionsRequestType;
          }>;
        };
      }
    | {__typename: 'InstigationStateNotFoundError'}
    | {__typename: 'PythonError'};
};

export const SelectedTickQueryVersion = '10c228399d8224b30ce4520d24f0c6f675a534abc7cbe268b0c8cc870b3f0e90';
