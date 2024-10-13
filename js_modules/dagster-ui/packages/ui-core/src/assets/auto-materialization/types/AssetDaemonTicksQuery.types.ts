// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetDaemonTickFragment = {
  __typename: 'InstigationTick';
  id: string;
  timestamp: number;
  endTimestamp: number | null;
  status: Types.InstigationTickStatus;
  instigationType: Types.InstigationType;
  requestedAssetMaterializationCount: number;
  autoMaterializeAssetEvaluationId: number | null;
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

export type AssetDaemonTicksQueryVariables = Types.Exact<{
  dayRange?: Types.InputMaybe<Types.Scalars['Int']['input']>;
  dayOffset?: Types.InputMaybe<Types.Scalars['Int']['input']>;
  statuses?: Types.InputMaybe<Array<Types.InstigationTickStatus> | Types.InstigationTickStatus>;
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
  beforeTimestamp?: Types.InputMaybe<Types.Scalars['Float']['input']>;
  afterTimestamp?: Types.InputMaybe<Types.Scalars['Float']['input']>;
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
    autoMaterializeAssetEvaluationId: number | null;
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
