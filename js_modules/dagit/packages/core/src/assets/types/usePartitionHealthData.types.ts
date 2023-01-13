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
        partitionMaterializationCounts:
          | {
              __typename: 'MaterializationCountGroupedByDimension';
              materializationCountsGrouped: Array<Array<number>>;
            }
          | {
              __typename: 'MaterializationCountSingleDimension';
              materializationCounts: Array<number>;
            };
      }
    | {__typename: 'AssetNotFoundError'};
};
