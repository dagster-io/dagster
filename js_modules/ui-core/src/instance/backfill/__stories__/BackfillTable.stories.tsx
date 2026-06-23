import {MockedProvider} from '@apollo/client/testing';

import {BackfillTable} from '../BackfillTable';
import {
  BackfillTableFragmentCompletedAssetJobStatus,
  BackfillTableFragmentCompletedOpJobStatus,
  BackfillTableFragmentFailedErrorStatus,
  BackfillTableFragments,
} from '../__fixtures__/BackfillTable.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Instance/BackfillTable',
  component: BackfillTable,
};

export const GeneralStates = () => {
  return (
    <MockedProvider
      mocks={[
        BackfillTableFragmentCompletedOpJobStatus,
        BackfillTableFragmentCompletedAssetJobStatus,
        BackfillTableFragmentFailedErrorStatus,
      ]}
    >
      <BackfillTable backfills={BackfillTableFragments} refetch={() => {}} />
    </MockedProvider>
  );
};
