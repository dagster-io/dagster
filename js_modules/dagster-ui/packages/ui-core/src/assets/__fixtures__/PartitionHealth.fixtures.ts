import {PartitionDefinitionType, PartitionRangeStatus} from '../../graphql/types';
import {PartitionHealthQuery} from '../types/usePartitionHealthData.types';

export const DIMENSION_ONE_KEYS = [
  '2022-01-01',
  '2022-01-02',
  '2022-01-03',
  '2022-01-04',
  '2022-01-05',
  '2022-01-06',
];

export const DIMENSION_TWO_KEYS = ['TN', 'CA', 'VA', 'NY', 'MN'];

export const NO_DIMENSIONAL_ASSET: PartitionHealthQuery = {
  __typename: 'Query',
  assetNodeOrError: {
    __typename: 'AssetNode',
    id: '1234',
    partitionKeysByDimension: [],
    assetPartitionStatuses: {
      __typename: 'DefaultPartitionStatuses',
      materializedPartitions: [],
      materializingPartitions: [],
      failedPartitions: [],
    },
  },
};

export const ONE_DIMENSIONAL_ASSET: PartitionHealthQuery = {
  __typename: 'Query',
  assetNodeOrError: {
    __typename: 'AssetNode',
    id: '1234',
    partitionKeysByDimension: [
      {
        __typename: 'DimensionPartitionKeys',
        name: 'default',
        partitionKeys: DIMENSION_ONE_KEYS,
        type: PartitionDefinitionType.TIME_WINDOW,
      },
    ],
    assetPartitionStatuses: {
      __typename: 'TimePartitionStatuses',
      ranges: [
        {
          __typename: 'TimePartitionRangeStatus',
          status: PartitionRangeStatus.MATERIALIZED,
          startKey: '2022-01-04',
          startTime: new Date('2022-01-04').getTime(),
          endKey: '2022-01-05',
          endTime: new Date('2022-01-04').getTime(),
        },
        {
          __typename: 'TimePartitionRangeStatus',
          status: PartitionRangeStatus.FAILED,
          startKey: '2022-01-05',
          startTime: new Date('2022-01-05').getTime(),
          endKey: '2022-01-06',
          endTime: new Date('2022-01-06').getTime(),
        },
      ],
    },
  },
};

export const TWO_DIMENSIONAL_ASSET: PartitionHealthQuery = {
  __typename: 'Query',
  assetNodeOrError: {
    __typename: 'AssetNode',
    id: '1234',
    partitionKeysByDimension: [
      {
        __typename: 'DimensionPartitionKeys',
        name: 'time',
        partitionKeys: DIMENSION_ONE_KEYS,
        type: PartitionDefinitionType.TIME_WINDOW,
      },
      {
        __typename: 'DimensionPartitionKeys',
        name: 'state',
        partitionKeys: DIMENSION_TWO_KEYS,
        type: PartitionDefinitionType.STATIC,
      },
    ],
    assetPartitionStatuses: {
      __typename: 'MultiPartitionStatuses',
      primaryDimensionName: 'time',
      ranges: [
        {
          __typename: 'MaterializedPartitionRangeStatuses2D',
          primaryDimStartKey: '2022-01-01',
          primaryDimStartTime: new Date('2022-01-01').getTime(),
          primaryDimEndKey: '2022-01-01',
          primaryDimEndTime: new Date('2022-01-01').getTime(),
          secondaryDim: {
            __typename: 'DefaultPartitionStatuses',
            materializedPartitions: ['NY', 'MN'],
            materializingPartitions: [],
            failedPartitions: [],
          },
        },
        {
          __typename: 'MaterializedPartitionRangeStatuses2D',
          primaryDimStartKey: '2022-01-02',
          primaryDimStartTime: new Date('2022-01-02').getTime(),
          primaryDimEndKey: '2022-01-03',
          primaryDimEndTime: new Date('2022-01-03').getTime(),
          secondaryDim: {
            __typename: 'DefaultPartitionStatuses',
            materializedPartitions: ['MN'],
            materializingPartitions: [],
            failedPartitions: [],
          },
        },
        {
          __typename: 'MaterializedPartitionRangeStatuses2D',
          primaryDimStartKey: '2022-01-04',
          primaryDimStartTime: new Date('2022-01-04').getTime(),
          primaryDimEndKey: '2022-01-04',
          primaryDimEndTime: new Date('2022-01-04').getTime(),
          secondaryDim: {
            __typename: 'DefaultPartitionStatuses',
            materializedPartitions: ['TN', 'CA', 'VA', 'NY', 'MN'],
            materializingPartitions: [],
            failedPartitions: [],
          },
        },
        {
          __typename: 'MaterializedPartitionRangeStatuses2D',
          primaryDimStartKey: '2022-01-05',
          primaryDimStartTime: new Date('2022-01-05').getTime(),
          primaryDimEndKey: '2022-01-06',
          primaryDimEndTime: new Date('2022-01-06').getTime(),
          secondaryDim: {
            __typename: 'DefaultPartitionStatuses',
            materializedPartitions: ['MN'],
            materializingPartitions: [],
            failedPartitions: ['NY', 'VA'],
          },
        },
      ],
    },
  },
};

export const TWO_DIMENSIONAL_ASSET_REVERSED_DIMENSIONS: PartitionHealthQuery = {
  __typename: 'Query',
  assetNodeOrError: {
    __typename: 'AssetNode',
    id: '1234',
    partitionKeysByDimension: [
      {
        __typename: 'DimensionPartitionKeys',
        name: 'state',
        partitionKeys: DIMENSION_TWO_KEYS,
        type: PartitionDefinitionType.STATIC,
      },
      {
        __typename: 'DimensionPartitionKeys',
        name: 'time',
        partitionKeys: DIMENSION_ONE_KEYS,
        type: PartitionDefinitionType.TIME_WINDOW,
      },
    ],
    assetPartitionStatuses: {
      __typename: 'MultiPartitionStatuses',
      primaryDimensionName: 'time',
      ranges: [
        {
          __typename: 'MaterializedPartitionRangeStatuses2D',
          primaryDimStartKey: '2022-01-01',
          primaryDimStartTime: new Date('2022-01-01').getTime(),
          primaryDimEndKey: '2022-01-01',
          primaryDimEndTime: new Date('2022-01-01').getTime(),
          secondaryDim: {
            __typename: 'DefaultPartitionStatuses',
            materializedPartitions: ['NY', 'MN'],
            materializingPartitions: [],
            failedPartitions: [],
          },
        },
        {
          __typename: 'MaterializedPartitionRangeStatuses2D',
          primaryDimStartKey: '2022-01-02',
          primaryDimStartTime: new Date('2022-01-02').getTime(),
          primaryDimEndKey: '2022-01-03',
          primaryDimEndTime: new Date('2022-01-03').getTime(),
          secondaryDim: {
            __typename: 'DefaultPartitionStatuses',
            materializedPartitions: ['MN'],
            materializingPartitions: [],
            failedPartitions: [],
          },
        },
        {
          __typename: 'MaterializedPartitionRangeStatuses2D',
          primaryDimStartKey: '2022-01-04',
          primaryDimStartTime: new Date('2022-01-04').getTime(),
          primaryDimEndKey: '2022-01-04',
          primaryDimEndTime: new Date('2022-01-04').getTime(),
          secondaryDim: {
            __typename: 'DefaultPartitionStatuses',
            materializedPartitions: ['TN', 'CA', 'VA', 'NY', 'MN'],
            materializingPartitions: [],
            failedPartitions: [],
          },
        },
        {
          __typename: 'MaterializedPartitionRangeStatuses2D',
          primaryDimStartKey: '2022-01-05',
          primaryDimStartTime: new Date('2022-01-05').getTime(),
          primaryDimEndKey: '2022-01-06',
          primaryDimEndTime: new Date('2022-01-06').getTime(),
          secondaryDim: {
            __typename: 'DefaultPartitionStatuses',
            materializedPartitions: ['MN'],
            materializingPartitions: [],
            failedPartitions: ['NY', 'VA'],
          },
        },
      ],
    },
  },
};

export const TWO_DIMENSIONAL_ASSET_BOTH_STATIC: PartitionHealthQuery = {
  __typename: 'Query',
  assetNodeOrError: {
    __typename: 'AssetNode',
    id: '1234',
    partitionKeysByDimension: [
      {
        __typename: 'DimensionPartitionKeys',
        name: 'state1',
        partitionKeys: DIMENSION_TWO_KEYS,
        type: PartitionDefinitionType.STATIC,
      },
      {
        __typename: 'DimensionPartitionKeys',
        name: 'state2',
        partitionKeys: DIMENSION_TWO_KEYS,
        type: PartitionDefinitionType.STATIC,
      },
    ],
    assetPartitionStatuses: {
      __typename: 'MultiPartitionStatuses',
      primaryDimensionName: 'state1',
      ranges: [
        {
          __typename: 'MaterializedPartitionRangeStatuses2D',
          primaryDimStartKey: 'TN',
          primaryDimEndKey: 'CA',
          primaryDimEndTime: null,
          primaryDimStartTime: null,
          secondaryDim: {
            __typename: 'DefaultPartitionStatuses',
            materializedPartitions: ['TN', 'CA', 'VA'],
            materializingPartitions: [],
            failedPartitions: ['MN'],
          },
        },
        {
          __typename: 'MaterializedPartitionRangeStatuses2D',
          primaryDimStartKey: 'VA',
          primaryDimEndKey: 'MN',
          primaryDimEndTime: null,
          primaryDimStartTime: null,
          secondaryDim: {
            __typename: 'DefaultPartitionStatuses',
            materializedPartitions: ['CA', 'MN'],
            materializingPartitions: [],
            failedPartitions: [],
          },
        },
      ],
    },
  },
};

export const TWO_DIMENSIONAL_ASSET_EMPTY: PartitionHealthQuery = {
  __typename: 'Query',
  assetNodeOrError: {
    __typename: 'AssetNode',
    id: '1234',
    partitionKeysByDimension: [
      {
        __typename: 'DimensionPartitionKeys',
        name: 'time',
        partitionKeys: DIMENSION_ONE_KEYS,
        type: PartitionDefinitionType.STATIC,
      },
      {
        __typename: 'DimensionPartitionKeys',
        name: 'state',
        partitionKeys: DIMENSION_TWO_KEYS,
        type: PartitionDefinitionType.STATIC,
      },
    ],
    assetPartitionStatuses: {
      __typename: 'MultiPartitionStatuses',
      primaryDimensionName: 'time',
      ranges: [],
    },
  },
};

export const ONE_DIMENSIONAL_DYNAMIC_ASSET: PartitionHealthQuery = {
  __typename: 'Query',
  assetNodeOrError: {
    __typename: 'AssetNode',
    id: '1234',
    partitionKeysByDimension: [
      {
        __typename: 'DimensionPartitionKeys',
        name: 'default',
        partitionKeys: ['apple', 'pear', 'fig'],
        type: PartitionDefinitionType.DYNAMIC,
      },
    ],
    assetPartitionStatuses: {
      __typename: 'DefaultPartitionStatuses',
      materializedPartitions: ['apple', 'pear', 'fig'],
      materializingPartitions: [],
      failedPartitions: [],
    },
  },
};
