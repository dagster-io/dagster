import {PartitionHealthQueryQuery} from '../graphql/graphql';
import {PartitionState} from '../partitions/PartitionStatus';

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

const ONE_DIMENSIONAL_ASSET: PartitionHealthQueryQuery = {
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
    partitionMaterializationCounts: {
      __typename: 'MaterializationCountSingleDimension',
      materializationCounts: [0, 0, 0, 1, 1, 0],
    },
  },
};

const TWO_DIMENSIONAL_ASSET: PartitionHealthQueryQuery = {
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
    partitionMaterializationCounts: {
      __typename: 'MaterializationCountGroupedByDimension',
      materializationCountsGrouped: [
        //               TN,CA,VA,NY,MN
        /* 2022-01-01 */ [0, 0, 0, 1, 1],
        /* 2022-01-02 */ [0, 0, 0, 0, 1],
        /* 2022-01-03 */ [0, 0, 0, 0, 1],
        /* 2022-01-04 */ [1, 1, 1, 1, 1],
        /* 2022-01-05 */ [0, 0, 0, 0, 1],
        /* 2022-01-06 */ [0, 0, 0, 0, 1],
      ],
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

      expect(assetHealth.stateForPartialKey(['2022-01-01'])).toEqual(MISSING);
      expect(assetHealth.stateForPartialKey(['2022-01-04'])).toEqual(SUCCESS);

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

      // Ask for the state of a partial key (row)
      expect(assetHealth.stateForPartialKey(['2022-01-01'])).toEqual(SUCCESS_MISSING);

      // Ask for the state of a row
      expect(assetHealth.stateForSingleDimension(0, '2022-01-03')).toEqual(SUCCESS_MISSING);
      expect(assetHealth.stateForSingleDimension(0, '2022-01-04')).toEqual(SUCCESS);

      // Ask for the state of a column
      expect(assetHealth.stateForSingleDimension(1, 'TN')).toEqual(SUCCESS_MISSING);
      expect(assetHealth.stateForSingleDimension(1, 'MN')).toEqual(SUCCESS);
    });
  });
});
