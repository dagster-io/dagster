import {MockedProvider} from '@apollo/client/testing';

import {LaunchAssetChoosePartitionsDialog} from '../LaunchAssetChoosePartitionsDialog';
import {ReleasesJobProps} from '../__fixtures__/LaunchAssetChoosePartitionsDialog.fixtures';
import {
  ReleaseFiles,
  ReleaseFilesMetadata,
  ReleaseZips,
  ReleasesMetadata,
  ReleasesSummary,
} from '../__fixtures__/PartitionHealthQuery.fixtures';
import {NoRunningBackfills} from '../__fixtures__/RunningBackfillsNoticeQuery.fixture';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Assets/LaunchAssetChoosePartitionsDialog',
  component: LaunchAssetChoosePartitionsDialog,
};

export const Empty = () => {
  return (
    <MockedProvider
      mocks={[
        ReleaseFiles(true),
        ReleaseFilesMetadata(true),
        ReleaseZips(true),
        ReleasesMetadata(true),
        ReleasesSummary(true),
        NoRunningBackfills,
      ]}
    >
      <LaunchAssetChoosePartitionsDialog
        {...ReleasesJobProps}
        open={true}
        setOpen={function () {}}
      />
    </MockedProvider>
  );
};

export const Ordinal = () => {
  return (
    <MockedProvider
      mocks={[
        ReleaseFiles(),
        ReleaseFilesMetadata(),
        ReleaseZips(),
        ReleasesMetadata(),
        ReleasesSummary(),
        NoRunningBackfills,
      ]}
    >
      <LaunchAssetChoosePartitionsDialog
        {...ReleasesJobProps}
        open={true}
        setOpen={function () {}}
      />
    </MockedProvider>
  );
};
