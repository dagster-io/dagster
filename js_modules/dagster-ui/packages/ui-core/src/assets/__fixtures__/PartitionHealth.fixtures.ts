import {
  PartitionDefinitionType,
  PartitionRangeStatus,
  buildAssetNode,
  buildDefaultPartitionStatuses,
  buildDimensionPartitionKeys,
  buildMaterializedPartitionRangeStatuses2D,
  buildMultiPartitionStatuses,
  buildQuery,
  buildTimePartitionRangeStatus,
  buildTimePartitionStatuses,
} from '../../graphql/types';
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

export const NO_DIMENSIONAL_ASSET: PartitionHealthQuery = buildQuery({
  assetNodeOrError: buildAssetNode({
    id: '1234',
    partitionKeysByDimension: [],
    assetPartitionStatuses: buildDefaultPartitionStatuses({
      materializedPartitions: [],
      materializingPartitions: [],
      failedPartitions: [],
    }),
  }),
});

export const ONE_DIMENSIONAL_ASSET: PartitionHealthQuery = buildQuery({
  assetNodeOrError: buildAssetNode({
    id: '1234',
    partitionKeysByDimension: [
      buildDimensionPartitionKeys({
        name: 'default',
        partitionKeys: DIMENSION_ONE_KEYS,
        type: PartitionDefinitionType.TIME_WINDOW,
      }),
    ],
    assetPartitionStatuses: buildTimePartitionStatuses({
      ranges: [
        buildTimePartitionRangeStatus({
          status: PartitionRangeStatus.MATERIALIZED,
          startKey: '2022-01-04',
          startTime: new Date('2022-01-04').getTime(),
          endKey: '2022-01-05',
          endTime: new Date('2022-01-04').getTime(),
        }),
        buildTimePartitionRangeStatus({
          status: PartitionRangeStatus.FAILED,
          startKey: '2022-01-05',
          startTime: new Date('2022-01-05').getTime(),
          endKey: '2022-01-06',
          endTime: new Date('2022-01-06').getTime(),
        }),
      ],
    }),
  }),
});

export const TWO_DIMENSIONAL_ASSET: PartitionHealthQuery = buildQuery({
  assetNodeOrError: buildAssetNode({
    id: '1234',
    partitionKeysByDimension: [
      buildDimensionPartitionKeys({
        name: 'time',
        partitionKeys: DIMENSION_ONE_KEYS,
        type: PartitionDefinitionType.TIME_WINDOW,
      }),
      buildDimensionPartitionKeys({
        name: 'state',
        partitionKeys: DIMENSION_TWO_KEYS,
        type: PartitionDefinitionType.STATIC,
      }),
    ],
    assetPartitionStatuses: buildMultiPartitionStatuses({
      primaryDimensionName: 'time',
      ranges: [
        buildMaterializedPartitionRangeStatuses2D({
          primaryDimStartKey: '2022-01-01',
          primaryDimStartTime: new Date('2022-01-01').getTime(),
          primaryDimEndKey: '2022-01-01',
          primaryDimEndTime: new Date('2022-01-01').getTime(),
          secondaryDim: buildDefaultPartitionStatuses({
            materializedPartitions: ['NY', 'MN'],
            materializingPartitions: [],
            failedPartitions: [],
          }),
        }),
        buildMaterializedPartitionRangeStatuses2D({
          primaryDimStartKey: '2022-01-02',
          primaryDimStartTime: new Date('2022-01-02').getTime(),
          primaryDimEndKey: '2022-01-03',
          primaryDimEndTime: new Date('2022-01-03').getTime(),
          secondaryDim: buildDefaultPartitionStatuses({
            materializedPartitions: ['MN'],
            materializingPartitions: [],
            failedPartitions: [],
          }),
        }),
        buildMaterializedPartitionRangeStatuses2D({
          primaryDimStartKey: '2022-01-04',
          primaryDimStartTime: new Date('2022-01-04').getTime(),
          primaryDimEndKey: '2022-01-04',
          primaryDimEndTime: new Date('2022-01-04').getTime(),
          secondaryDim: buildDefaultPartitionStatuses({
            materializedPartitions: ['TN', 'CA', 'VA', 'NY', 'MN'],
            materializingPartitions: [],
            failedPartitions: [],
          }),
        }),
        buildMaterializedPartitionRangeStatuses2D({
          primaryDimStartKey: '2022-01-05',
          primaryDimStartTime: new Date('2022-01-05').getTime(),
          primaryDimEndKey: '2022-01-06',
          primaryDimEndTime: new Date('2022-01-06').getTime(),
          secondaryDim: buildDefaultPartitionStatuses({
            materializedPartitions: ['MN'],
            materializingPartitions: [],
            failedPartitions: ['NY', 'VA'],
          }),
        }),
      ],
    }),
  }),
});

export const TWO_DIMENSIONAL_ASSET_REVERSED_DIMENSIONS: PartitionHealthQuery = buildQuery({
  assetNodeOrError: buildAssetNode({
    id: '1234',
    partitionKeysByDimension: [
      buildDimensionPartitionKeys({
        name: 'state',
        partitionKeys: DIMENSION_TWO_KEYS,
        type: PartitionDefinitionType.STATIC,
      }),
      buildDimensionPartitionKeys({
        name: 'time',
        partitionKeys: DIMENSION_ONE_KEYS,
        type: PartitionDefinitionType.TIME_WINDOW,
      }),
    ],
    assetPartitionStatuses: buildMultiPartitionStatuses({
      primaryDimensionName: 'time',
      ranges: [
        buildMaterializedPartitionRangeStatuses2D({
          primaryDimStartKey: '2022-01-01',
          primaryDimStartTime: new Date('2022-01-01').getTime(),
          primaryDimEndKey: '2022-01-01',
          primaryDimEndTime: new Date('2022-01-01').getTime(),
          secondaryDim: buildDefaultPartitionStatuses({
            materializedPartitions: ['NY', 'MN'],
            materializingPartitions: [],
            failedPartitions: [],
          }),
        }),
        buildMaterializedPartitionRangeStatuses2D({
          primaryDimStartKey: '2022-01-02',
          primaryDimStartTime: new Date('2022-01-02').getTime(),
          primaryDimEndKey: '2022-01-03',
          primaryDimEndTime: new Date('2022-01-03').getTime(),
          secondaryDim: buildDefaultPartitionStatuses({
            materializedPartitions: ['MN'],
            materializingPartitions: [],
            failedPartitions: [],
          }),
        }),
        buildMaterializedPartitionRangeStatuses2D({
          primaryDimStartKey: '2022-01-04',
          primaryDimStartTime: new Date('2022-01-04').getTime(),
          primaryDimEndKey: '2022-01-04',
          primaryDimEndTime: new Date('2022-01-04').getTime(),
          secondaryDim: buildDefaultPartitionStatuses({
            materializedPartitions: ['TN', 'CA', 'VA', 'NY', 'MN'],
            materializingPartitions: [],
            failedPartitions: [],
          }),
        }),
        buildMaterializedPartitionRangeStatuses2D({
          primaryDimStartKey: '2022-01-05',
          primaryDimStartTime: new Date('2022-01-05').getTime(),
          primaryDimEndKey: '2022-01-06',
          primaryDimEndTime: new Date('2022-01-06').getTime(),
          secondaryDim: buildDefaultPartitionStatuses({
            materializedPartitions: ['MN'],
            materializingPartitions: [],
            failedPartitions: ['NY', 'VA'],
          }),
        }),
      ],
    }),
  }),
});

export const TWO_DIMENSIONAL_ASSET_BOTH_STATIC: PartitionHealthQuery = buildQuery({
  assetNodeOrError: buildAssetNode({
    id: '1234',
    partitionKeysByDimension: [
      buildDimensionPartitionKeys({
        name: 'state1',
        partitionKeys: DIMENSION_TWO_KEYS,
        type: PartitionDefinitionType.STATIC,
      }),
      buildDimensionPartitionKeys({
        name: 'state2',
        partitionKeys: DIMENSION_TWO_KEYS,
        type: PartitionDefinitionType.STATIC,
      }),
    ],
    assetPartitionStatuses: buildMultiPartitionStatuses({
      primaryDimensionName: 'state1',
      ranges: [
        buildMaterializedPartitionRangeStatuses2D({
          primaryDimStartKey: 'TN',
          primaryDimEndKey: 'CA',
          primaryDimEndTime: null,
          primaryDimStartTime: null,
          secondaryDim: buildDefaultPartitionStatuses({
            materializedPartitions: ['TN', 'CA', 'VA'],
            materializingPartitions: [],
            failedPartitions: ['MN'],
          }),
        }),
        buildMaterializedPartitionRangeStatuses2D({
          primaryDimStartKey: 'VA',
          primaryDimEndKey: 'MN',
          primaryDimEndTime: null,
          primaryDimStartTime: null,
          secondaryDim: buildDefaultPartitionStatuses({
            materializedPartitions: ['CA', 'MN'],
            materializingPartitions: [],
            failedPartitions: [],
          }),
        }),
      ],
    }),
  }),
});

export const TWO_DIMENSIONAL_ASSET_EMPTY: PartitionHealthQuery = buildQuery({
  assetNodeOrError: buildAssetNode({
    id: '1234',
    partitionKeysByDimension: [
      buildDimensionPartitionKeys({
        name: 'time',
        partitionKeys: DIMENSION_ONE_KEYS,
        type: PartitionDefinitionType.STATIC,
      }),
      buildDimensionPartitionKeys({
        name: 'state',
        partitionKeys: DIMENSION_TWO_KEYS,
        type: PartitionDefinitionType.STATIC,
      }),
    ],
    assetPartitionStatuses: buildMultiPartitionStatuses({
      primaryDimensionName: 'time',
      ranges: [],
    }),
  }),
});

export const ONE_DIMENSIONAL_DYNAMIC_ASSET: PartitionHealthQuery = buildQuery({
  assetNodeOrError: buildAssetNode({
    id: '1234',
    partitionKeysByDimension: [
      buildDimensionPartitionKeys({
        name: 'default',
        partitionKeys: ['apple', 'pear', 'fig'],
        type: PartitionDefinitionType.DYNAMIC,
      }),
    ],
    assetPartitionStatuses: buildDefaultPartitionStatuses({
      materializedPartitions: ['apple', 'pear', 'fig'],
      materializingPartitions: [],
      failedPartitions: [],
    }),
  }),
});
