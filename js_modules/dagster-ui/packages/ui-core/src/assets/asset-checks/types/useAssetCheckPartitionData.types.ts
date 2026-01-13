// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetCheckPartitionHealthQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  checkName: Types.Scalars['String']['input'];
}>;

export type AssetCheckPartitionHealthQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        assetCheckOrError:
          | {
              __typename: 'AssetCheck';
              name: string;
              partitionKeysByDimension: Array<{
                __typename: 'DimensionPartitionKeys';
                name: string;
                partitionKeys: Array<string>;
              }>;
              partitionStatuses:
                | {
                    __typename: 'AssetCheckDefaultPartitionStatuses';
                    succeededPartitions: Array<string>;
                    failedPartitions: Array<string>;
                    inProgressPartitions: Array<string>;
                    skippedPartitions: Array<string>;
                    executionFailedPartitions: Array<string>;
                  }
                | {
                    __typename: 'AssetCheckMultiPartitionStatuses';
                    primaryDimensionName: string;
                    ranges: Array<{
                      __typename: 'AssetCheckMultiPartitionRangeStatuses';
                      primaryDimStartKey: string;
                      primaryDimEndKey: string;
                      primaryDimStartTime: number | null;
                      primaryDimEndTime: number | null;
                      secondaryDim:
                        | {
                            __typename: 'AssetCheckDefaultPartitionStatuses';
                            succeededPartitions: Array<string>;
                            failedPartitions: Array<string>;
                            inProgressPartitions: Array<string>;
                            skippedPartitions: Array<string>;
                            executionFailedPartitions: Array<string>;
                          }
                        | {
                            __typename: 'AssetCheckTimePartitionStatuses';
                            ranges: Array<{
                              __typename: 'AssetCheckTimePartitionRangeStatus';
                              startTime: number;
                              endTime: number;
                              startKey: string;
                              endKey: string;
                              status: Types.AssetCheckPartitionRangeStatus;
                            }>;
                          };
                    }>;
                  }
                | {
                    __typename: 'AssetCheckTimePartitionStatuses';
                    ranges: Array<{
                      __typename: 'AssetCheckTimePartitionRangeStatus';
                      startTime: number;
                      endTime: number;
                      startKey: string;
                      endKey: string;
                      status: Types.AssetCheckPartitionRangeStatus;
                    }>;
                  }
                | null;
            }
          | {__typename: 'AssetCheckNeedsAgentUpgradeError'}
          | {__typename: 'AssetCheckNeedsMigrationError'}
          | {__typename: 'AssetCheckNeedsUserCodeUpgrade'}
          | {__typename: 'AssetCheckNotFoundError'};
      }
    | {__typename: 'AssetNotFoundError'};
};

export const AssetCheckPartitionHealthQueryVersion = '52d785ffa4da993a6a04b76f8cbb61fe6f315346f639a5ec1b3cb58d9fa4e7d6';
