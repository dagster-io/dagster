// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SelectedTickQueryVariables = Types.Exact<{
  instigationSelector: Types.InstigationSelector;
  tickId: Types.Scalars['ID']['input'];
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
