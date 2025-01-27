import {MockedProvider} from '@apollo/client/testing';

import {
  buildAssetKey,
  buildAssetNode,
  buildBackfillPolicy,
  buildPartitionDefinition,
} from '../../graphql/types';
import {BackfillPreviewDialog} from '../BackfillPreviewDialog';
import {
  BackfillPreviewQueryMock,
  BackfillPreviewQueryMockPartitionKeys,
} from '../__fixtures__/BackfillPreviewQuery.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Assets/BackfillPreviewDialog',
  component: BackfillPreviewDialog,
};

const MOCKS = [BackfillPreviewQueryMock];

export const PartitionMappedBackfillPreview = () => {
  return (
    <MockedProvider mocks={MOCKS}>
      <BackfillPreviewDialog
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
