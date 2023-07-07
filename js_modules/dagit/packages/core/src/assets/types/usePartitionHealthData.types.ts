// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PartitionHealthQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
}>;

export type PartitionHealthQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        partitionKeysByDimension: Array<{
          __typename: 'DimensionPartitionKeys';
          name: string;
          type: Types.PartitionDefinitionType;
          partitionKeys: Array<string>;
        }>;
        assetPartitionStatuses:
          | {
              __typename: 'DefaultPartitionStatuses';
              materializedPartitions: Array<string>;
              materializingPartitions: Array<string>;
              failedPartitions: Array<string>;
            }
          | {
              __typename: 'MultiPartitionStatuses';
              primaryDimensionName: string;
              ranges: Array<{
                __typename: 'MaterializedPartitionRangeStatuses2D';
                primaryDimStartKey: string;
                primaryDimEndKey: string;
                primaryDimStartTime: number | null;
                primaryDimEndTime: number | null;
                secondaryDim:
                  | {
                      __typename: 'DefaultPartitionStatuses';
                      materializedPartitions: Array<string>;
                      materializingPartitions: Array<string>;
                      failedPartitions: Array<string>;
                    }
                  | {
                      __typename: 'TimePartitionStatuses';
                      ranges: Array<{
                        __typename: 'TimePartitionRangeStatus';
                        status: Types.PartitionRangeStatus;
                        startTime: number;
                        endTime: number;
                        startKey: string;
                        endKey: string;
                      }>;
                    };
              }>;
            }
          | {
              __typename: 'TimePartitionStatuses';
              ranges: Array<{
                __typename: 'TimePartitionRangeStatus';
                status: Types.PartitionRangeStatus;
                startTime: number;
                endTime: number;
                startKey: string;
                endKey: string;
              }>;
            };
      }
    | {__typename: 'AssetNotFoundError'};
};
