import {PartitionState} from '../partitions/PartitionStatus';

import {PartitionHealthQuery} from './types/usePartitionHealthData.types';
import {
  Range,
  buildPartitionHealthData,
  PartitionDimensionSelectionRange,
  partitionStatusGivenRanges,
  rangeClippedToSelection,
  rangesForKeys,
} from './usePartitionHealthData';

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

      expect(assetHealth.rangesForSingleDimension(0)).toEqual([
        {
          start: {idx: 3, key: '2022-01-04'},
          end: {idx: 4, key: '2022-01-05'},
          value: PartitionState.SUCCESS,
        },
      ]);

      // should not crash if asked for an invalid dimension -- just return []
      expect(assetHealth.rangesForSingleDimension(1)).toEqual([]);
      expect(assetHealth.rangesForSingleDimension(2)).toEqual([]);
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

      // Ask for the ranges of a row
      expect(assetHealth.rangesForSingleDimension(0)).toEqual([
        {
          start: {idx: 0, key: '2022-01-01'},
          end: {idx: 2, key: '2022-01-03'},
          value: PartitionState.SUCCESS_MISSING,
        },
        {
          start: {idx: 3, key: '2022-01-04'},
          end: {idx: 3, key: '2022-01-04'},
          value: PartitionState.SUCCESS,
        },
        {
          start: {idx: 4, key: '2022-01-05'},
          end: {idx: 5, key: '2022-01-06'},
          value: PartitionState.SUCCESS_MISSING,
        },
      ]);

      expect(
        assetHealth.rangesForSingleDimension(0, [
          [
            {key: 'MN', idx: 4},
            {key: 'MN', idx: 4},
          ],
        ]),
      ).toEqual([
        {
          start: {idx: 0, key: '2022-01-01'},
          end: {idx: 5, key: '2022-01-06'},
          value: PartitionState.SUCCESS,
        },
      ]);

      expect(
        assetHealth.rangesForSingleDimension(0, [
          [
            {key: 'NY', idx: 3},
            {key: 'MN', idx: 4},
          ],
        ]),
      ).toEqual([
        {
          start: {idx: 0, key: '2022-01-01'},
          end: {idx: 0, key: '2022-01-01'},
          value: PartitionState.SUCCESS,
        },
        {
          start: {idx: 1, key: '2022-01-02'},
          end: {idx: 2, key: '2022-01-03'},
          value: PartitionState.SUCCESS_MISSING,
        },
        {
          start: {idx: 3, key: '2022-01-04'},
          end: {idx: 3, key: '2022-01-04'},
          value: PartitionState.SUCCESS,
        },
        {
          start: {idx: 4, key: '2022-01-05'},
          end: {idx: 5, key: '2022-01-06'},
          value: PartitionState.SUCCESS_MISSING,
        },
      ]);

      expect(assetHealth.rangesForSingleDimension(1)).toEqual([
        {
          start: {idx: 0, key: 'TN'},
          end: {idx: 3, key: 'NY'},
          value: PartitionState.SUCCESS_MISSING,
        },
        {
          start: {idx: 4, key: 'MN'},
          end: {idx: 4, key: 'MN'},
          value: PartitionState.SUCCESS,
        },
      ]);

      expect(
        assetHealth.rangesForSingleDimension(1, [
          [
            {key: '2022-01-01', idx: 0},
            {key: '2022-01-01', idx: 0},
          ],
        ]),
      ).toEqual([
        {
          start: {idx: 3, key: 'NY'},
          end: {idx: 4, key: 'MN'},
          value: PartitionState.SUCCESS,
        },
      ]);

      // should not crash if asked for an invalid dimension -- just return []
      expect(assetHealth.rangesForSingleDimension(2)).toEqual([]);
    });

    it('should return correct data in all-missing states', async () => {
      const assetHealth = buildPartitionHealthData(TWO_DIMENSIONAL_ASSET_EMPTY, {path: ['asset']});
      expect(assetHealth.assetKey).toEqual({path: ['asset']});

      expect(assetHealth.stateForKey(['2022-01-01', 'TN'])).toEqual(MISSING);
      expect(assetHealth.stateForKey(['2022-01-04', 'NY'])).toEqual(MISSING);

      expect(assetHealth.stateForSingleDimension(0, '2022-01-03')).toEqual(MISSING);
      expect(assetHealth.stateForSingleDimension(1, 'TN')).toEqual(MISSING);

      expect(assetHealth.rangesForSingleDimension(0)).toEqual([]);
      expect(
        assetHealth.rangesForSingleDimension(0, [
          [
            {key: 'NY', idx: 3},
            {key: 'MN', idx: 4},
          ],
        ]),
      ).toEqual([]);

      expect(assetHealth.rangesForSingleDimension(1)).toEqual([]);
      expect(
        assetHealth.rangesForSingleDimension(1, [
          [
            {key: '2022-01-01', idx: 0},
            {key: '2022-01-01', idx: 0},
          ],
        ]),
      ).toEqual([]);
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

const KEYS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'];

const A_F: Range = {
  start: {idx: 0, key: 'A'},
  end: {idx: 5, key: 'F'},
  value: PartitionState.SUCCESS,
};
const A_C: Range = {
  start: {idx: 0, key: 'A'},
  end: {key: 'C', idx: 2},
  value: PartitionState.SUCCESS,
};
const A_I: Range = {
  start: {idx: 0, key: 'A'},
  end: {idx: 8, key: 'I'},
  value: PartitionState.SUCCESS,
};
const B_E: Range = {
  start: {idx: 1, key: 'B'},
  end: {idx: 4, key: 'E'},
  value: PartitionState.SUCCESS,
};
const G_I: Range = {
  start: {idx: 6, key: 'G'},
  end: {idx: 8, key: 'I'},
  value: PartitionState.SUCCESS,
};

const SEL_A_C: PartitionDimensionSelectionRange = [
  {key: 'A', idx: 0},
  {key: 'C', idx: 2},
];
const SEL_A_D: PartitionDimensionSelectionRange = [
  {key: 'A', idx: 0},
  {key: 'D', idx: 3},
];
const SEL_C_D: PartitionDimensionSelectionRange = [
  {key: 'C', idx: 2},
  {key: 'D', idx: 3},
];
const SEL_E_G: PartitionDimensionSelectionRange = [
  {key: 'E', idx: 4},
  {key: 'G', idx: 6},
];
const SEL_G_G: PartitionDimensionSelectionRange = [
  {key: 'G', idx: 6},
  {key: 'G', idx: 6},
];

describe('usePartitionHealthData utilities', () => {
  describe('partitionStatusGivenRanges', () => {
    it('should return SUCCESS if the ranges span the total key count', () => {
      expect(partitionStatusGivenRanges([A_I], KEYS.length)).toEqual(PartitionState.SUCCESS);
      expect(partitionStatusGivenRanges([A_F, G_I], KEYS.length)).toEqual(PartitionState.SUCCESS);
    });

    it('should return SUCCESS_MISSING if the ranges are not empty', () => {
      expect(partitionStatusGivenRanges([A_F], KEYS.length)).toEqual(
        PartitionState.SUCCESS_MISSING,
      );
      expect(partitionStatusGivenRanges([G_I], KEYS.length)).toEqual(
        PartitionState.SUCCESS_MISSING,
      );
    });

    it('should return MISSING if the ranges are empty', () => {
      expect(partitionStatusGivenRanges([], KEYS.length)).toEqual(PartitionState.MISSING);
    });
  });

  describe('rangeClippedToSelection', () => {
    it('should clip the range to a selection specifying one sub-section of it', () => {
      expect(rangeClippedToSelection(B_E, [SEL_C_D])).toEqual([
        {
          start: {key: 'C', idx: 2},
          end: {key: 'D', idx: 3},
          value: PartitionState.SUCCESS,
        },
      ]);
    });

    it('should clip the range to a selection specifying one end of it', () => {
      expect(rangeClippedToSelection(B_E, [SEL_A_D])).toEqual([
        {
          start: {key: 'B', idx: 1},
          end: {key: 'D', idx: 3},
          value: PartitionState.SUCCESS,
        },
      ]);
    });

    it('should clip the range to a selection specifying both ends but not the middle', () => {
      expect(rangeClippedToSelection(B_E, [SEL_A_C, SEL_E_G])).toEqual([
        {
          start: {key: 'B', idx: 1},
          end: {key: 'C', idx: 2},
          value: PartitionState.SUCCESS,
        },
        {
          start: {key: 'E', idx: 4},
          end: {key: 'E', idx: 4},
          value: PartitionState.SUCCESS,
        },
      ]);
    });

    it('should clip the range to a selection that does not overlap with the range at all', () => {
      expect(rangeClippedToSelection(B_E, [SEL_G_G])).toEqual([]);
    });

    it('should not alter the input data', () => {
      const before = JSON.stringify({B_E, SEL_A_D});
      rangeClippedToSelection(B_E, [SEL_A_D]);
      expect(JSON.stringify({B_E, SEL_A_D})).toEqual(before);
    });
  });

  describe('rangesForKeys', () => {
    it('should return a complete range given all dimension keys', () => {
      expect(rangesForKeys(KEYS, KEYS)).toEqual([A_I]);
    });
    it('should return the correct result if `keys` is unsorted', () => {
      expect(rangesForKeys(['A', 'C', 'B', 'D', 'F', 'G', 'I', 'H', 'E'], KEYS)).toEqual([A_I]);
    });
    it('should return several ranges if there are segments in `keys`', () => {
      expect(rangesForKeys(['B', 'C', 'D', 'E'], KEYS)).toEqual([B_E]);
      expect(rangesForKeys(['A', 'B', 'C', 'G', 'H', 'I'], KEYS)).toEqual([A_C, G_I]);
      expect(rangesForKeys(['G'], KEYS)).toEqual([
        {start: {idx: 6, key: 'G'}, end: {idx: 6, key: 'G'}, value: PartitionState.SUCCESS},
      ]);
    });
    it('should return no ranges if no keys are provided', () => {
      expect(rangesForKeys([], KEYS)).toEqual([]);
    });
  });
});
