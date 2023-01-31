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
          partitionKeys: Array<string>;
        }>;
        materializedPartitions:
          | {__typename: 'DefaultPartitions'; materializedPartitions: Array<string>}
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
                  | {__typename: 'DefaultPartitions'; materializedPartitions: Array<string>}
                  | {
                      __typename: 'TimePartitions';
                      ranges: Array<{
                        __typename: 'TimePartitionRange';
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
                startTime: number;
                endTime: number;
                startKey: string;
                endKey: string;
              }>;
            };
      }
    | {__typename: 'AssetNotFoundError'};
};

export type PartitionHealthMaterialized1DPartitionsFragment_DefaultPartitions_ = {
  __typename: 'DefaultPartitions';
  materializedPartitions: Array<string>;
};

export type PartitionHealthMaterialized1DPartitionsFragment_TimePartitions_ = {
  __typename: 'TimePartitions';
  ranges: Array<{
    __typename: 'TimePartitionRange';
    startTime: number;
    endTime: number;
    startKey: string;
    endKey: string;
  }>;
};

export type PartitionHealthMaterialized1DPartitionsFragment =
  | PartitionHealthMaterialized1DPartitionsFragment_DefaultPartitions_
  | PartitionHealthMaterialized1DPartitionsFragment_TimePartitions_;

export type PartitionHealthMaterializedPartitionsFragment_DefaultPartitions_ = {
  __typename: 'DefaultPartitions';
  materializedPartitions: Array<string>;
};

export type PartitionHealthMaterializedPartitionsFragment_MultiPartitions_ = {
  __typename: 'MultiPartitions';
  primaryDimensionName: string;
  ranges: Array<{
    __typename: 'MaterializedPartitionRange2D';
    primaryDimStartKey: string;
    primaryDimEndKey: string;
    primaryDimStartTime: number | null;
    primaryDimEndTime: number | null;
    secondaryDim:
      | {__typename: 'DefaultPartitions'; materializedPartitions: Array<string>}
      | {
          __typename: 'TimePartitions';
          ranges: Array<{
            __typename: 'TimePartitionRange';
            startTime: number;
            endTime: number;
            startKey: string;
            endKey: string;
          }>;
        };
  }>;
};

export type PartitionHealthMaterializedPartitionsFragment_TimePartitions_ = {
  __typename: 'TimePartitions';
  ranges: Array<{
    __typename: 'TimePartitionRange';
    startTime: number;
    endTime: number;
    startKey: string;
    endKey: string;
  }>;
};

export type PartitionHealthMaterializedPartitionsFragment =
  | PartitionHealthMaterializedPartitionsFragment_DefaultPartitions_
  | PartitionHealthMaterializedPartitionsFragment_MultiPartitions_
  | PartitionHealthMaterializedPartitionsFragment_TimePartitions_;
