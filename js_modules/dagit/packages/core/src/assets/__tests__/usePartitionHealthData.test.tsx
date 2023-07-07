import {PartitionDefinitionType, PartitionRangeStatus} from '../../graphql/types';
import {AssetPartitionStatus, emptyAssetPartitionStatusCounts} from '../AssetPartitionStatus';
import {PartitionHealthQuery} from '../types/usePartitionHealthData.types';
import {
  Range,
  buildPartitionHealthData,
  PartitionDimensionSelectionRange,
  partitionStatusGivenRanges,
  rangeClippedToSelection,
  rangesForKeys,
  partitionStatusAtIndex,
  keyCountByStateInSelection,
  PartitionHealthDimension,
  PartitionDimensionSelection,
  keyCountInRanges,
} from '../usePartitionHealthData';

const {MATERIALIZED, FAILED, MISSING} = AssetPartitionStatus;

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

const ONE_DIMENSIONAL_ASSET: PartitionHealthQuery = {
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

const TWO_DIMENSIONAL_ASSET: PartitionHealthQuery = {
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

const TWO_DIMENSIONAL_ASSET_BOTH_STATIC: PartitionHealthQuery = {
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

const TWO_DIMENSIONAL_ASSET_EMPTY: PartitionHealthQuery = {
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

function selectionWithSlice(
  dim: PartitionHealthDimension,
  start: number,
  end: number,
): PartitionDimensionSelection {
  return {
    dimension: dim,
    selectedKeys: dim.partitionKeys.slice(start, end + 1),
    selectedRanges: [
      {
        start: {idx: start, key: dim.partitionKeys[start]!},
        end: {idx: end, key: dim.partitionKeys[end]!},
      },
    ],
  };
}

describe('usePartitionHealthData', () => {
  describe('loadPartitionHealthData', () => {
    it('should return an object with accessors for 1D partition data', async () => {
      const assetHealth = buildPartitionHealthData(ONE_DIMENSIONAL_ASSET, {path: ['asset']});
      expect(assetHealth.assetKey).toEqual({path: ['asset']});
      expect(assetHealth.dimensions).toEqual([
        {
          name: 'default',
          partitionKeys: DIMENSION_ONE_KEYS,
          type: 'TIME_WINDOW',
        },
      ]);

      expect(assetHealth.stateForKey(['2022-01-01'])).toEqual(MISSING);
      expect(assetHealth.stateForKey(['2022-01-04'])).toEqual(MATERIALIZED);

      expect(assetHealth.rangesForSingleDimension(0)).toEqual([
        {
          start: {idx: 3, key: '2022-01-04'},
          end: {idx: 4, key: '2022-01-05'},
          value: [AssetPartitionStatus.MATERIALIZED],
        },
        {
          start: {idx: 4, key: '2022-01-05'},
          end: {idx: 5, key: '2022-01-06'},
          value: [AssetPartitionStatus.FAILED],
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
          type: 'TIME_WINDOW',
        },
        {
          name: 'state',
          partitionKeys: DIMENSION_TWO_KEYS,
          type: 'STATIC',
        },
      ]);

      // Ask for the state of a full key (cell)
      expect(assetHealth.stateForKey(['2022-01-01', 'TN'])).toEqual(MISSING);
      expect(assetHealth.stateForKey(['2022-01-04', 'NY'])).toEqual(MATERIALIZED);
      expect(assetHealth.stateForKey(['2022-01-05', 'NY'])).toEqual(FAILED);
      expect(assetHealth.stateForKey(['2022-01-05', 'MN'])).toEqual(MATERIALIZED);

      // Ask for the ranges of a row
      expect(assetHealth.rangesForSingleDimension(0)).toEqual([
        {
          start: {idx: 0, key: '2022-01-01'},
          end: {idx: 2, key: '2022-01-03'},
          value: [AssetPartitionStatus.MATERIALIZED, AssetPartitionStatus.MISSING],
        },
        {
          start: {idx: 3, key: '2022-01-04'},
          end: {idx: 3, key: '2022-01-04'},
          value: [AssetPartitionStatus.MATERIALIZED],
        },
        {
          start: {idx: 4, key: '2022-01-05'},
          end: {idx: 5, key: '2022-01-06'},
          value: [
            AssetPartitionStatus.MATERIALIZED,
            AssetPartitionStatus.FAILED,
            AssetPartitionStatus.MISSING,
          ],
        },
      ]);

      // Ask for ranges of a row, clipped to a column selection
      expect(
        assetHealth.rangesForSingleDimension(0, [
          {start: {key: 'MN', idx: 4}, end: {key: 'MN', idx: 4}},
        ]),
      ).toEqual([
        {
          start: {idx: 0, key: '2022-01-01'},
          end: {idx: 5, key: '2022-01-06'},
          value: [AssetPartitionStatus.MATERIALIZED],
        },
      ]);

      // Ask for ranges of a row, clipped to a column selection
      expect(
        assetHealth.rangesForSingleDimension(0, [
          {start: {key: 'NY', idx: 3}, end: {key: 'MN', idx: 4}},
        ]),
      ).toEqual([
        {
          start: {idx: 0, key: '2022-01-01'},
          end: {idx: 0, key: '2022-01-01'},
          value: [AssetPartitionStatus.MATERIALIZED],
        },
        {
          start: {idx: 1, key: '2022-01-02'},
          end: {idx: 2, key: '2022-01-03'},
          value: [AssetPartitionStatus.MATERIALIZED, AssetPartitionStatus.MISSING],
        },
        {
          start: {idx: 3, key: '2022-01-04'},
          end: {idx: 3, key: '2022-01-04'},
          value: [AssetPartitionStatus.MATERIALIZED],
        },
        {
          start: {idx: 4, key: '2022-01-05'},
          end: {idx: 5, key: '2022-01-06'},
          value: [AssetPartitionStatus.MATERIALIZED, AssetPartitionStatus.FAILED],
        },
      ]);

      // Ask for ranges of a row, clipped to an empty column selection
      expect(assetHealth.rangesForSingleDimension(0, [])).toEqual([]);

      // Ask for ranges of a column
      expect(assetHealth.rangesForSingleDimension(1)).toEqual([
        {
          start: {idx: 0, key: 'TN'},
          end: {idx: 1, key: 'CA'},
          value: [AssetPartitionStatus.MATERIALIZED, AssetPartitionStatus.MISSING],
        },
        {
          start: {idx: 2, key: 'VA'},
          end: {idx: 3, key: 'NY'},
          value: [
            AssetPartitionStatus.FAILED,
            AssetPartitionStatus.MATERIALIZED,
            AssetPartitionStatus.MISSING,
          ],
        },
        {
          start: {idx: 4, key: 'MN'},
          end: {idx: 4, key: 'MN'},
          value: [AssetPartitionStatus.MATERIALIZED],
        },
      ]);

      // Ask for ranges of a column, clipped to a row selection
      expect(
        assetHealth.rangesForSingleDimension(1, [
          {
            start: {key: '2022-01-01', idx: 0},
            end: {key: '2022-01-01', idx: 0},
          },
        ]),
      ).toEqual([
        {
          start: {idx: 3, key: 'NY'},
          end: {idx: 4, key: 'MN'},
          value: [AssetPartitionStatus.MATERIALIZED],
        },
      ]);

      // Ask for ranges of a column, clipped to an empty row selection
      expect(assetHealth.rangesForSingleDimension(1, [])).toEqual([]);

      // should not crash if asked for an invalid dimension -- just return []
      expect(assetHealth.rangesForSingleDimension(2)).toEqual([]);
    });

    it('should return correct data in all-missing states', async () => {
      const assetHealth = buildPartitionHealthData(TWO_DIMENSIONAL_ASSET_EMPTY, {path: ['asset']});
      expect(assetHealth.assetKey).toEqual({path: ['asset']});

      expect(assetHealth.stateForKey(['2022-01-01', 'TN'])).toEqual(MISSING);
      expect(assetHealth.stateForKey(['2022-01-04', 'NY'])).toEqual(MISSING);

      expect(assetHealth.rangesForSingleDimension(0)).toEqual([]);
      expect(
        assetHealth.rangesForSingleDimension(0, [
          {
            start: {key: 'NY', idx: 3},
            end: {key: 'MN', idx: 4},
          },
        ]),
      ).toEqual([]);

      expect(assetHealth.rangesForSingleDimension(1)).toEqual([]);
      expect(
        assetHealth.rangesForSingleDimension(1, [
          {
            start: {key: '2022-01-01', idx: 0},
            end: {key: '2022-01-01', idx: 0},
          },
        ]),
      ).toEqual([]);
    });

    it('should return an object with accessors for 2D partition data where both are static', async () => {
      const assetHealth = buildPartitionHealthData(TWO_DIMENSIONAL_ASSET_BOTH_STATIC, {
        path: ['asset'],
      });
      expect(assetHealth.assetKey).toEqual({path: ['asset']});
      expect(assetHealth.stateForKey(['TN', 'TN'])).toEqual(MATERIALIZED);
      expect(assetHealth.stateForKey(['CA', 'NY'])).toEqual(MISSING);
    });

    it('should return correct (empty) data if the asset is not partitioned at all', async () => {
      const assetHealth = buildPartitionHealthData(NO_DIMENSIONAL_ASSET, {path: ['asset']});
      expect(assetHealth.assetKey).toEqual({path: ['asset']});
      expect(assetHealth.dimensions).toEqual([]);

      // These should safely no-op
      expect(assetHealth.stateForKey(['2022-01-01'])).toEqual(MISSING);
    });
  });
});

const KEYS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'];

const A_F: Range = {
  start: {idx: 0, key: 'A'},
  end: {idx: 5, key: 'F'},
  value: [AssetPartitionStatus.MATERIALIZED],
};
const A_C: Range = {
  start: {idx: 0, key: 'A'},
  end: {key: 'C', idx: 2},
  value: [AssetPartitionStatus.MATERIALIZED],
};
const A_I: Range = {
  start: {idx: 0, key: 'A'},
  end: {idx: 8, key: 'I'},
  value: [AssetPartitionStatus.MATERIALIZED],
};
const B_E: Range = {
  start: {idx: 1, key: 'B'},
  end: {idx: 4, key: 'E'},
  value: [AssetPartitionStatus.MATERIALIZED],
};
const G_I: Range = {
  start: {idx: 6, key: 'G'},
  end: {idx: 8, key: 'I'},
  value: [AssetPartitionStatus.MATERIALIZED],
};

const SEL_A_C: PartitionDimensionSelectionRange = {
  start: {key: 'A', idx: 0},
  end: {key: 'C', idx: 2},
};
const SEL_A_D: PartitionDimensionSelectionRange = {
  start: {key: 'A', idx: 0},
  end: {key: 'D', idx: 3},
};
const SEL_C_D: PartitionDimensionSelectionRange = {
  start: {key: 'C', idx: 2},
  end: {key: 'D', idx: 3},
};
const SEL_E_G: PartitionDimensionSelectionRange = {
  start: {key: 'E', idx: 4},
  end: {key: 'G', idx: 6},
};
const SEL_G_G: PartitionDimensionSelectionRange = {
  start: {key: 'G', idx: 6},
  end: {key: 'G', idx: 6},
};

describe('usePartitionHealthData utilities', () => {
  describe('partitionStatusGivenRanges', () => {
    it('should return SUCCESS if the ranges span the total key count', () => {
      expect(partitionStatusGivenRanges([A_I], KEYS.length)).toEqual([
        AssetPartitionStatus.MATERIALIZED,
      ]);
      expect(partitionStatusGivenRanges([A_F, G_I], KEYS.length)).toEqual([
        AssetPartitionStatus.MATERIALIZED,
      ]);
    });

    it('should return SUCCESS_MISSING if the ranges are not empty', () => {
      expect(partitionStatusGivenRanges([A_F], KEYS.length)).toEqual([
        AssetPartitionStatus.MATERIALIZED,
        AssetPartitionStatus.MISSING,
      ]);
      expect(partitionStatusGivenRanges([G_I], KEYS.length)).toEqual([
        AssetPartitionStatus.MATERIALIZED,
        AssetPartitionStatus.MISSING,
      ]);
    });

    it('should return MISSING if the ranges are empty', () => {
      expect(partitionStatusGivenRanges([], KEYS.length)).toEqual([AssetPartitionStatus.MISSING]);
    });
  });

  describe('rangeClippedToSelection', () => {
    it('should clip the range to a selection specifying one sub-section of it', () => {
      expect(rangeClippedToSelection(B_E, [SEL_C_D])).toEqual([
        {
          start: {key: 'C', idx: 2},
          end: {key: 'D', idx: 3},
          value: [AssetPartitionStatus.MATERIALIZED],
        },
      ]);
    });

    it('should clip the range to a selection specifying one end of it', () => {
      expect(rangeClippedToSelection(B_E, [SEL_A_D])).toEqual([
        {
          start: {key: 'B', idx: 1},
          end: {key: 'D', idx: 3},
          value: [AssetPartitionStatus.MATERIALIZED],
        },
      ]);
    });

    it('should clip the range to a selection specifying both ends but not the middle', () => {
      expect(rangeClippedToSelection(B_E, [SEL_A_C, SEL_E_G])).toEqual([
        {
          start: {key: 'B', idx: 1},
          end: {key: 'C', idx: 2},
          value: [AssetPartitionStatus.MATERIALIZED],
        },
        {
          start: {key: 'E', idx: 4},
          end: {key: 'E', idx: 4},
          value: [AssetPartitionStatus.MATERIALIZED],
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

  describe('keyCountInRanges', () => {
    it('should return 0 if passed no ranges', () => {
      expect(keyCountInRanges([])).toEqual(0);
    });
    it('should return the sum of the lengths of the ranges', () => {
      expect(keyCountInRanges([A_C, G_I])).toEqual(6);
    });
  });

  describe('rangesForKeys', () => {
    it('should return a complete range given all dimension keys', () => {
      expect(rangesForKeys(KEYS, KEYS)).toEqual([A_I]);
    });
    it('should return an empty range if all dimension keys is an empty array', () => {
      expect(rangesForKeys([], [])).toEqual([]);
      expect(rangesForKeys(KEYS, [])).toEqual([]);
    });
    it('should return the correct result if `keys` is unsorted', () => {
      expect(rangesForKeys(['A', 'C', 'B', 'D', 'F', 'G', 'I', 'H', 'E'], KEYS)).toEqual([A_I]);
    });
    it('should return several ranges if there are segments in `keys`', () => {
      expect(rangesForKeys(['B', 'C', 'D', 'E'], KEYS)).toEqual([B_E]);
      expect(rangesForKeys(['A', 'B', 'C', 'G', 'H', 'I'], KEYS)).toEqual([A_C, G_I]);
      expect(rangesForKeys(['G'], KEYS)).toEqual([
        {
          start: {idx: 6, key: 'G'},
          end: {idx: 6, key: 'G'},
          value: [AssetPartitionStatus.MATERIALIZED],
        },
      ]);
    });
    it('should return no ranges if no keys are provided', () => {
      expect(rangesForKeys([], KEYS)).toEqual([]);
    });
  });

  describe('partitionStatusAtIndex', () => {
    it('should return range.value if the index is within one of the ranges, missing otherwise', () => {
      expect(partitionStatusAtIndex([A_C, G_I], 0)).toEqual([AssetPartitionStatus.MATERIALIZED]);
      expect(partitionStatusAtIndex([A_C, G_I], 6)).toEqual([AssetPartitionStatus.MATERIALIZED]);
      expect(partitionStatusAtIndex([A_C, G_I], 3)).toEqual([AssetPartitionStatus.MISSING]);
      expect(partitionStatusAtIndex([A_C, G_I], -1)).toEqual([AssetPartitionStatus.MISSING]);
      expect(partitionStatusAtIndex([A_C, G_I], 100)).toEqual([AssetPartitionStatus.MISSING]);
      expect(partitionStatusAtIndex([], 3)).toEqual([AssetPartitionStatus.MISSING]);
      expect(partitionStatusAtIndex([], -1)).toEqual([AssetPartitionStatus.MISSING]);
      expect(partitionStatusAtIndex([], 100)).toEqual([AssetPartitionStatus.MISSING]);
      expect(
        partitionStatusAtIndex(
          [
            {
              start: {idx: 0, key: 'A'},
              end: {idx: 8, key: 'G'},
              value: [AssetPartitionStatus.MATERIALIZED, AssetPartitionStatus.MISSING],
            },
          ],
          2,
        ),
      ).toEqual([AssetPartitionStatus.MATERIALIZED, AssetPartitionStatus.MISSING]);
    });
  });

  describe('keyCountByStateInSelection', () => {
    it('should return nothing when passed an empty selection array (invalid use)', () => {
      const one = buildPartitionHealthData(ONE_DIMENSIONAL_ASSET, {path: ['asset']});
      expect(keyCountByStateInSelection(one, [])).toEqual(emptyAssetPartitionStatusCounts());
    });

    it('should return correct counts in the one dimensional case', () => {
      const one = buildPartitionHealthData(ONE_DIMENSIONAL_ASSET, {path: ['asset']});

      expect(
        keyCountByStateInSelection(one, [selectionWithSlice(one.dimensions[0]!, 0, 5)]),
      ).toEqual({
        ...emptyAssetPartitionStatusCounts(),
        [AssetPartitionStatus.FAILED]: 2,
        [AssetPartitionStatus.MISSING]: 2,
        [AssetPartitionStatus.MATERIALIZED]: 2,
      });

      expect(
        keyCountByStateInSelection(one, [selectionWithSlice(one.dimensions[0]!, 0, 2)]),
      ).toEqual({
        ...emptyAssetPartitionStatusCounts(),
        [AssetPartitionStatus.MISSING]: 3,
      });
    });

    it('should return correct counts in the two dimensional case', () => {
      const two = buildPartitionHealthData(TWO_DIMENSIONAL_ASSET, {path: ['asset']});

      expect(
        keyCountByStateInSelection(two, [
          selectionWithSlice(two.dimensions[0]!, 0, 5),
          selectionWithSlice(two.dimensions[1]!, 0, 4),
        ]),
      ).toEqual({
        ...emptyAssetPartitionStatusCounts(),
        [AssetPartitionStatus.FAILED]: 4,
        [AssetPartitionStatus.MISSING]: 15,
        [AssetPartitionStatus.MATERIALIZED]: 11,
      });

      expect(
        keyCountByStateInSelection(two, [
          selectionWithSlice(two.dimensions[0]!, 0, 3),
          selectionWithSlice(two.dimensions[1]!, 0, 3),
        ]),
      ).toEqual({
        ...emptyAssetPartitionStatusCounts(),
        [AssetPartitionStatus.MISSING]: 11,
        [AssetPartitionStatus.MATERIALIZED]: 5,
      });

      expect(
        keyCountByStateInSelection(two, [
          selectionWithSlice(two.dimensions[0]!, 0, 5),
          selectionWithSlice(two.dimensions[1]!, 4, 4),
        ]),
      ).toEqual({
        ...emptyAssetPartitionStatusCounts(),
        [AssetPartitionStatus.MATERIALIZED]: 6,
      });
    });

    it('should return correct counts in the empty case', () => {
      const twoEmpty = buildPartitionHealthData(TWO_DIMENSIONAL_ASSET_EMPTY, {path: ['asset']});

      expect(
        keyCountByStateInSelection(twoEmpty, [
          selectionWithSlice(twoEmpty.dimensions[0]!, 0, 5),
          selectionWithSlice(twoEmpty.dimensions[1]!, 0, 4),
        ]),
      ).toEqual({
        ...emptyAssetPartitionStatusCounts(),
        [AssetPartitionStatus.MISSING]: 30,
      });
    });
  });
});
