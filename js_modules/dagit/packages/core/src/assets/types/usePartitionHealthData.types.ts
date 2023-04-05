// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PartitionHealthQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
}>;

export type PartitionHealthQuery = {
  __typename: 'DagitQuery';
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
              __typename: 'DefaultPartitions';
              materializedPartitions: Array<string>;
              materializingPartitions: Array<string>;
              failedPartitions: Array<string>;
            }
          | {
              __typename: 'MultiPartitions';
              primaryDimensionName: string;
              ranges: Array<{
                __typename: 'MaterializedPartitionRange2D';
                primaryDimStartKey: string;
                primaryDimEndKey: string;
                primaryDimStartTime: number | null;
                primaryDimEndTime: number | null;
                secondaryDim:
                  | {
                      __typename: 'DefaultPartitions';
                      materializedPartitions: Array<string>;
                      materializingPartitions: Array<string>;
                      failedPartitions: Array<string>;
                    }
                  | {
                      __typename: 'TimePartitions';
                      ranges: Array<{
                        __typename: 'TimePartitionRange';
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
              __typename: 'TimePartitions';
              ranges: Array<{
                __typename: 'TimePartitionRange';
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
