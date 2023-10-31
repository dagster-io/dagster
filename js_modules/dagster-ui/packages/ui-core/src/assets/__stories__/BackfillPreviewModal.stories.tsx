import {MockedProvider} from '@apollo/client/testing';
import React from 'react';

import {
  buildAssetKey,
  buildAssetNode,
  buildBackfillPolicy,
  buildPartitionDefinition,
} from '../../graphql/types';
import {BackfillPreviewModal} from '../BackfillPreviewModal';
import {
  BackfillPreviewQueryMock,
  BackfillPreviewQueryMockPartitionKeys,
} from '../__fixtures__/BackfillPreviewQuery.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Assets/BackfillPreviewModal',
  component: BackfillPreviewModal,
};

const MOCKS = [BackfillPreviewQueryMock];

export const PartitionMappedBackfillPreview = () => {
  return (
    <MockedProvider mocks={MOCKS}>
      <BackfillPreviewModal
        isOpen={true}
        setOpen={() => {}}
        assets={[
          buildAssetNode({
            assetKey: buildAssetKey({path: ['asset_weekly']}),
            partitionDefinition: buildPartitionDefinition({
              description: 'Weekly at 4:00AM UTC',
            }),
            backfillPolicy: buildBackfillPolicy({
              description: 'Backfills using separate runs, with at most 5 partitions per run.',
            }),
          }),
          buildAssetNode({
            assetKey: buildAssetKey({path: ['asset_daily']}),
            partitionDefinition: buildPartitionDefinition({
              description: 'Daily at 4:00AM UTC',
            }),
            backfillPolicy: buildBackfillPolicy({
              description: 'Backfills in a single run.',
            }),
          }),
        ]}
        keysFiltered={BackfillPreviewQueryMockPartitionKeys}
      />
    </MockedProvider>
  );
};
