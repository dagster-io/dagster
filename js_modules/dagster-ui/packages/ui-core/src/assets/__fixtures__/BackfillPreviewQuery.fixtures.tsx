import {MockedResponse} from '@apollo/client/testing';

import {
  buildQuery,
  buildAssetPartitions,
  buildAssetKey,
  buildAssetBackfillTargetPartitions,
  buildPartitionKeyRange,
} from '../../graphql/types';
import {BACKFILL_PREVIEW_QUERY} from '../BackfillPreviewModal';
import {
  BackfillPreviewQuery,
  BackfillPreviewQueryVariables,
} from '../types/BackfillPreviewModal.types';

export const BackfillPreviewQueryMockPartitionKeys = [
  '2023-07-02',
  '2023-07-09',
  '2023-07-16',
  '2023-07-23',
  '2023-07-30',
  '2023-08-06',
  '2023-08-13',
  '2023-08-20',
  '2023-08-27',
  '2023-09-03',
  '2023-09-10',
  '2023-09-17',
  '2023-09-24',
  '2023-10-01',
  '2023-10-08',
  '2023-10-15',
  '2023-10-22',
];

export const BackfillPreviewQueryMock: MockedResponse<
  BackfillPreviewQuery,
  BackfillPreviewQueryVariables
> = {
  request: {
    query: BACKFILL_PREVIEW_QUERY,
    variables: {
      partitionNames: BackfillPreviewQueryMockPartitionKeys,
      assetKeys: [{path: ['asset_weekly']}, {path: ['asset_daily']}],
    },
  },
  result: {
    data: buildQuery({
      assetBackfillPreview: [
        buildAssetPartitions({
          assetKey: buildAssetKey({path: ['asset_daily']}),
          partitions: buildAssetBackfillTargetPartitions({
            ranges: [buildPartitionKeyRange({start: '2023-07-02', end: '2023-10-22'})],
            partitionKeys: null,
          }),
        }),
        buildAssetPartitions({
          assetKey: buildAssetKey({path: ['asset_weekly']}),
          partitions: buildAssetBackfillTargetPartitions({
            ranges: [buildPartitionKeyRange({start: '2023-07-07', end: '2023-10-21'})],
            partitionKeys: null,
          }),
        }),
      ],
    }),
  },
};
