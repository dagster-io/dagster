import {MockedProvider} from '@apollo/client/testing';

import {StorybookProvider} from '../../../testing/StorybookProvider';
import {BackfillTable} from '../BackfillTable';
import {
  BackfillTableFragmentCancelledAssetsPartitionSetStatus,
  BackfillTableFragmentCompletedAssetJobStatus,
  BackfillTableFragmentCompletedOpJobStatus,
  BackfillTableFragmentFailedErrorStatus,
  BackfillTableFragmentRequested2000AssetsPureStatus,
  BackfillTableFragments,
} from '../__fixtures__/BackfillTable.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Instance/BackfillTable',
  component: BackfillTable,
};

export const GeneralStates = () => {
  return (
    <StorybookProvider>
      <MockedProvider
        mocks={[
          BackfillTableFragmentRequested2000AssetsPureStatus,
          BackfillTableFragmentCancelledAssetsPartitionSetStatus,
          BackfillTableFragmentCompletedOpJobStatus,
          BackfillTableFragmentCompletedAssetJobStatus,
          BackfillTableFragmentFailedErrorStatus,
        ]}
      >
        <BackfillTable backfills={BackfillTableFragments} refetch={() => {}} />
      </MockedProvider>
    </StorybookProvider>
  );
};
