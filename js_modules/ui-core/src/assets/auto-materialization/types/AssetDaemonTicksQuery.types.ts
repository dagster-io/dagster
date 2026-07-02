/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type InstigationTickStatus = 'FAILURE' | 'SKIPPED' | 'STARTED' | 'SUCCESS';

export type InstigationType = 'AUTO_MATERIALIZE' | 'SCHEDULE' | 'SENSOR';

export type AssetDaemonTickFragment = {
  __typename: 'InstigationTick';
  id: string;
  timestamp: number;
  endTimestamp: number | null;
  status: Types.InstigationTickStatus;
  instigationType: Types.InstigationType;
  requestedAssetMaterializationCount: number;
  autoMaterializeAssetEvaluationId: string | null;
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
  requestedAssetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
  requestedMaterializationsForAssets: Array<{
    __typename: 'RequestedMaterializationsForAsset';
    partitionKeys: Array<string>;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
  }>;
};

export type AssetDaemonTicksQueryVariables = Exact<{
  dayRange?: number | null | undefined;
  dayOffset?: number | null | undefined;
  statuses?: Array<Types.InstigationTickStatus> | Types.InstigationTickStatus | null | undefined;
  limit?: number | null | undefined;
  cursor?: string | null | undefined;
  beforeTimestamp?: number | null | undefined;
  afterTimestamp?: number | null | undefined;
}>;

export type AssetDaemonTicksQuery = {
  __typename: 'Query';
  autoMaterializeTicks: Array<{
    __typename: 'InstigationTick';
    id: string;
    timestamp: number;
    endTimestamp: number | null;
    status: Types.InstigationTickStatus;
    instigationType: Types.InstigationType;
    requestedAssetMaterializationCount: number;
    autoMaterializeAssetEvaluationId: string | null;
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
    requestedAssetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
    requestedMaterializationsForAssets: Array<{
      __typename: 'RequestedMaterializationsForAsset';
      partitionKeys: Array<string>;
      assetKey: {__typename: 'AssetKey'; path: Array<string>};
    }>;
  }>;
};

export const AssetDaemonTicksQueryVersion = '399ac77e660d40eba32c2ab06db2a2936a71e660d93ec108364eec1fdfc16788';
