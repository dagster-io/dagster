import {MockedProvider} from '@apollo/client/testing';
import {Button} from '@dagster-io/ui-components';

import {AnalyticsContext, dummyAnalytics} from '../../app/analytics';
import {buildWorkspaceMocks} from '../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {useSearchDialog} from '../SearchDialog';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'useSearchDialog',
};

const SearchDialog = () => {
  const {openSearch, overlay} = useSearchDialog();
  return (
    <>
      <Button onClick={openSearch}>Open</Button>
      {overlay}
    </>
  );
};

export const BasicSearch = () => (
  <AnalyticsContext.Provider value={dummyAnalytics()}>
    <MockedProvider mocks={buildWorkspaceMocks([])}>
      <SearchDialog />
    </MockedProvider>
  </AnalyticsContext.Provider>
);

export const SlowSecondaryQuerySearch = () => (
  <AnalyticsContext.Provider value={dummyAnalytics()}>
    <MockedProvider mocks={buildWorkspaceMocks([])}>
      <SearchDialog />
    </MockedProvider>
  </AnalyticsContext.Provider>
);

export const LotsOfAssetsSearch = () => (
  <AnalyticsContext.Provider value={dummyAnalytics()}>
    <MockedProvider mocks={buildWorkspaceMocks([])}>
      <SearchDialog />
    </MockedProvider>
  </AnalyticsContext.Provider>
);
