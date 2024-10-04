// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetSensorTicksQueryVariables = Types.Exact<{
  sensorSelector: Types.SensorSelector;
  dayRange?: Types.InputMaybe<Types.Scalars['Int']['input']>;
  dayOffset?: Types.InputMaybe<Types.Scalars['Int']['input']>;
  statuses?: Types.InputMaybe<Array<Types.InstigationTickStatus> | Types.InstigationTickStatus>;
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
  beforeTimestamp?: Types.InputMaybe<Types.Scalars['Float']['input']>;
  afterTimestamp?: Types.InputMaybe<Types.Scalars['Float']['input']>;
}>;

export type AssetSensorTicksQuery = {
  __typename: 'Query';
  sensorOrError:
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      }
    | {
        __typename: 'Sensor';
        id: string;
        sensorState: {
          __typename: 'InstigationState';
          id: string;
          ticks: Array<{
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
      }
    | {__typename: 'SensorNotFoundError'}
    | {__typename: 'UnauthorizedError'};
};

export const AssetSensorTicksQueryVersion = 'ee952c7c0076a23f9d5940ad472a6b580989c0d241dc598dbefa5bf3734673d0';
