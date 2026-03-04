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
                type: Types.PartitionDefinitionType;
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

export const AssetCheckPartitionHealthQueryVersion = 'd2843e7bc4b8d2cd5f625cf8de2a81c8a2603990cb3e294cf34782634caa3a6a';
