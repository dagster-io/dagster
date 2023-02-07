import {PartitionState} from '../partitions/PartitionStatus';

import {PartitionHealthQuery} from './types/usePartitionHealthData.types';
import {buildPartitionHealthData} from './usePartitionHealthData';

const {SUCCESS_MISSING, SUCCESS, MISSING} = PartitionState;

const DIMENSION_ONE_KEYS = [
  '2022-01-01',
  '2022-01-02',
  '2022-01-03',
  '2022-01-04',
  '2022-01-05',
  '2022-01-06',
];

const DIMENSION_TWO_KEYS = ['TN', 'CA', 'VA', 'NY', 'MN'];

const NO_DIMENSIONAL_ASSET: PartitionHealthQuery = {
  __typename: 'DagitQuery',
  assetNodeOrError: {
    __typename: 'AssetNode',
    id: '1234',
    partitionKeysByDimension: [],
    materializedPartitions: {
      __typename: 'DefaultPartitions',
      materializedPartitions: [],
    },
  },
};

const ONE_DIMENSIONAL_ASSET: PartitionHealthQuery = {
  __typename: 'DagitQuery',
  assetNodeOrError: {
    __typename: 'AssetNode',
    id: '1234',
    partitionKeysByDimension: [
      {
        __typename: 'DimensionPartitionKeys',
        name: 'default',
        partitionKeys: DIMENSION_ONE_KEYS,
      },
    ],
    materializedPartitions: {
      __typename: 'TimePartitions',
      ranges: [
        {
          __typename: 'TimePartitionRange',
          startKey: '2022-01-04',
          startTime: new Date('2022-01-04').getTime(),
          endKey: '2022-01-05',
          endTime: new Date('2022-01-04').getTime(),
        },
      ],
    },
  },
};

const TWO_DIMENSIONAL_ASSET: PartitionHealthQuery = {
  __typename: 'DagitQuery',
  assetNodeOrError: {
    __typename: 'AssetNode',
    id: '1234',
    partitionKeysByDimension: [
      {
        __typename: 'DimensionPartitionKeys',
        name: 'time',
        partitionKeys: DIMENSION_ONE_KEYS,
      },
      {
        __typename: 'DimensionPartitionKeys',
        name: 'state',
        partitionKeys: DIMENSION_TWO_KEYS,
      },
    ],
    materializedPartitions: {
      __typename: 'MultiPartitions',
      primaryDimensionName: 'time',
      ranges: [
        {
          __typename: 'MaterializedPartitionRange2D',
          primaryDimStartKey: '2022-01-01',
          primaryDimStartTime: new Date('2022-01-01').getTime(),
          primaryDimEndKey: '2022-01-01',
          primaryDimEndTime: new Date('2022-01-01').getTime(),
          secondaryDim: {
            __typename: 'DefaultPartitions',
            materializedPartitions: ['NY', 'MN'],
          },
        },
        {
          __typename: 'MaterializedPartitionRange2D',
          primaryDimStartKey: '2022-01-02',
          primaryDimStartTime: new Date('2022-01-02').getTime(),
          primaryDimEndKey: '2022-01-03',
          primaryDimEndTime: new Date('2022-01-03').getTime(),
          secondaryDim: {
            __typename: 'DefaultPartitions',
            materializedPartitions: ['MN'],
          },
        },
        {
          __typename: 'MaterializedPartitionRange2D',
          primaryDimStartKey: '2022-01-04',
          primaryDimStartTime: new Date('2022-01-04').getTime(),
          primaryDimEndKey: '2022-01-04',
          primaryDimEndTime: new Date('2022-01-04').getTime(),
          secondaryDim: {
            __typename: 'DefaultPartitions',
            materializedPartitions: ['TN', 'CA', 'VA', 'NY', 'MN'],
          },
        },
        {
          __typename: 'MaterializedPartitionRange2D',
          primaryDimStartKey: '2022-01-05',
          primaryDimStartTime: new Date('2022-01-05').getTime(),
          primaryDimEndKey: '2022-01-06',
          primaryDimEndTime: new Date('2022-01-06').getTime(),
          secondaryDim: {
            __typename: 'DefaultPartitions',
            materializedPartitions: ['MN'],
          },
        },
      ],
    },
  },
};

const TWO_DIMENSIONAL_ASSET_BOTH_STATIC: PartitionHealthQuery = {
  __typename: 'DagitQuery',
  assetNodeOrError: {
    __typename: 'AssetNode',
    id: '1234',
    partitionKeysByDimension: [
      {
        __typename: 'DimensionPartitionKeys',
        name: 'state1',
        partitionKeys: DIMENSION_TWO_KEYS,
      },
      {
        __typename: 'DimensionPartitionKeys',
        name: 'state2',
        partitionKeys: DIMENSION_TWO_KEYS,
      },
    ],
    materializedPartitions: {
      __typename: 'MultiPartitions',
      primaryDimensionName: 'state1',
      ranges: [
        {
          __typename: 'MaterializedPartitionRange2D',
          primaryDimStartKey: 'TN',
          primaryDimEndKey: 'CA',
          primaryDimEndTime: null,
          primaryDimStartTime: null,
          secondaryDim: {
            __typename: 'DefaultPartitions',
            materializedPartitions: ['TN', 'CA', 'VA'],
          },
        },
        {
          __typename: 'MaterializedPartitionRange2D',
          primaryDimStartKey: 'VA',
          primaryDimEndKey: 'MN',
          primaryDimEndTime: null,
          primaryDimStartTime: null,
          secondaryDim: {
            __typename: 'DefaultPartitions',
            materializedPartitions: ['CA', 'MN'],
          },
        },
      ],
    },
  },
};

const TWO_DIMENSIONAL_ASSET_EMPTY: PartitionHealthQuery = {
  __typename: 'DagitQuery',
  assetNodeOrError: {
    __typename: 'AssetNode',
    id: '1234',
    partitionKeysByDimension: [
      {
        __typename: 'DimensionPartitionKeys',
        name: 'time',
        partitionKeys: DIMENSION_ONE_KEYS,
      },
      {
        __typename: 'DimensionPartitionKeys',
        name: 'state',
        partitionKeys: DIMENSION_TWO_KEYS,
      },
    ],
    materializedPartitions: {
      __typename: 'MultiPartitions',
      primaryDimensionName: 'time',
      ranges: [],
    },
  },
};

describe('usePartitionHealthData', () => {
  describe('loadPartitionHealthData', () => {
    it('should return an object with accessors for 1D partition data', async () => {
      const assetHealth = buildPartitionHealthData(ONE_DIMENSIONAL_ASSET, {path: ['asset']});
      expect(assetHealth.assetKey).toEqual({path: ['asset']});
      expect(assetHealth.dimensions).toEqual([
        {
          name: 'default',
          partitionKeys: DIMENSION_ONE_KEYS,
        },
      ]);

      expect(assetHealth.stateForKey(['2022-01-01'])).toEqual(MISSING);
      expect(assetHealth.stateForKey(['2022-01-04'])).toEqual(SUCCESS);

      expect(assetHealth.stateForSingleDimension(0, '2022-01-01')).toEqual(MISSING);
      expect(assetHealth.stateForSingleDimension(0, '2022-01-04')).toEqual(SUCCESS);
    });

    it('should return an object with accessors for 2D partition data', async () => {
      const assetHealth = buildPartitionHealthData(TWO_DIMENSIONAL_ASSET, {path: ['asset']});
      expect(assetHealth.assetKey).toEqual({path: ['asset']});
      expect(assetHealth.dimensions).toEqual([
        {
          name: 'time',
          partitionKeys: DIMENSION_ONE_KEYS,
        },
        {
          name: 'state',
          partitionKeys: DIMENSION_TWO_KEYS,
        },
      ]);

      // Ask for the state of a full key (cell)
      expect(assetHealth.stateForKey(['2022-01-01', 'TN'])).toEqual(MISSING);
      expect(assetHealth.stateForKey(['2022-01-04', 'NY'])).toEqual(SUCCESS);

      // Ask for the state of a row
      expect(assetHealth.stateForSingleDimension(0, '2022-01-03')).toEqual(SUCCESS_MISSING);
      expect(assetHealth.stateForSingleDimension(0, '2022-01-04')).toEqual(SUCCESS);
      expect(assetHealth.stateForSingleDimension(0, '2022-01-01')).toEqual(SUCCESS_MISSING);
      expect(assetHealth.stateForSingleDimension(0, '2022-01-01', ['MN', 'NY'])).toEqual(SUCCESS);

      // Ask for the state of a column
      expect(assetHealth.stateForSingleDimension(1, 'TN')).toEqual(SUCCESS_MISSING);
      expect(assetHealth.stateForSingleDimension(1, 'MN')).toEqual(SUCCESS);
      expect(assetHealth.stateForSingleDimension(1, 'TN', ['2022-01-04'])).toEqual(SUCCESS);
    });

    it('should return correct data in all-missing states', async () => {
      const assetHealth = buildPartitionHealthData(TWO_DIMENSIONAL_ASSET_EMPTY, {path: ['asset']});
      expect(assetHealth.assetKey).toEqual({path: ['asset']});
      expect(assetHealth.stateForKey(['2022-01-01', 'TN'])).toEqual(MISSING);
      expect(assetHealth.stateForKey(['2022-01-04', 'NY'])).toEqual(MISSING);
      expect(assetHealth.stateForSingleDimension(0, '2022-01-03')).toEqual(MISSING);
      expect(assetHealth.stateForSingleDimension(1, 'TN')).toEqual(MISSING);
    });

    it('should return an object with accessors for 2D partition data where both are static', async () => {
      const assetHealth = buildPartitionHealthData(TWO_DIMENSIONAL_ASSET_BOTH_STATIC, {
        path: ['asset'],
      });
      expect(assetHealth.assetKey).toEqual({path: ['asset']});
      expect(assetHealth.stateForKey(['TN', 'TN'])).toEqual(SUCCESS);
      expect(assetHealth.stateForKey(['CA', 'NY'])).toEqual(MISSING);
      expect(assetHealth.stateForSingleDimension(0, 'CA')).toEqual(SUCCESS_MISSING);
      expect(assetHealth.stateForSingleDimension(0, 'CA', ['TN', 'CA'])).toEqual(SUCCESS);
      expect(assetHealth.stateForSingleDimension(0, 'CA', ['NY', 'MN'])).toEqual(MISSING);
      expect(assetHealth.stateForSingleDimension(1, 'TN')).toEqual(SUCCESS_MISSING);
      expect(assetHealth.stateForSingleDimension(1, 'TN', ['TN', 'CA'])).toEqual(SUCCESS);
      expect(assetHealth.stateForSingleDimension(1, 'CA')).toEqual(SUCCESS);
    });

    it('should return correct (empty) data if the asset is not partitioned at all', async () => {
      const assetHealth = buildPartitionHealthData(NO_DIMENSIONAL_ASSET, {path: ['asset']});
      expect(assetHealth.assetKey).toEqual({path: ['asset']});
      expect(assetHealth.dimensions).toEqual([]);

      // These should safely no-op
      expect(assetHealth.stateForKey(['2022-01-01'])).toEqual(MISSING);
      expect(assetHealth.stateForSingleDimension(0, '2022-01-01')).toEqual(MISSING);
    });
  });
});
