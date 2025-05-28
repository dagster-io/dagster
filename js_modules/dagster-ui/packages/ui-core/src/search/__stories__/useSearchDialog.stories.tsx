import {MockedProvider} from '@apollo/client/testing';
import {Button} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';

import {AnalyticsContext, dummyAnalytics} from '../../app/analytics';
import {useSearchDialog} from '../SearchDialog';
import {buildPrimarySearch, buildPrimarySearchStatic} from '../__fixtures__/Search.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'useSearchDialog',
} as Meta;

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
    <MockedProvider mocks={[buildPrimarySearchStatic()]}>
      <SearchDialog />
    </MockedProvider>
  </AnalyticsContext.Provider>
);

export const SlowSecondaryQuerySearch = () => (
  <AnalyticsContext.Provider value={dummyAnalytics()}>
    <MockedProvider mocks={[buildPrimarySearchStatic()]}>
      <SearchDialog />
    </MockedProvider>
  </AnalyticsContext.Provider>
);

export const LotsOfAssetsSearch = () => (
  <AnalyticsContext.Provider value={dummyAnalytics()}>
    <MockedProvider mocks={[buildPrimarySearch()]}>
      <SearchDialog />
    </MockedProvider>
  </AnalyticsContext.Provider>
);
