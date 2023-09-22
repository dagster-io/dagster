import {MockedProvider} from '@apollo/client/testing';
import {Meta} from '@storybook/react';
import * as React from 'react';

import {AnalyticsContext, dummyAnalytics} from '../../app/analytics';
import {SearchDialog} from '../SearchDialog';
import {
  buildPrimarySearch,
  buildPrimarySearchStatic,
  buildSecondarySearch,
  buildSecondarySearchStatic,
} from '../__fixtures__/Search.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'SearchDialog',
  component: SearchDialog,
} as Meta;

export const BasicSearch = () => (
  <AnalyticsContext.Provider value={dummyAnalytics()}>
    <MockedProvider mocks={[buildPrimarySearchStatic(), buildSecondarySearchStatic()]}>
      <SearchDialog searchPlaceholder="" />
    </MockedProvider>
  </AnalyticsContext.Provider>
);

export const SlowSecondaryQuerySearch = () => (
  <AnalyticsContext.Provider value={dummyAnalytics()}>
    <MockedProvider mocks={[buildPrimarySearchStatic(), buildSecondarySearchStatic(10000)]}>
      <SearchDialog searchPlaceholder="" />
    </MockedProvider>
  </AnalyticsContext.Provider>
);

export const LotsOfAssetsSearch = () => (
  <AnalyticsContext.Provider value={dummyAnalytics()}>
    <MockedProvider mocks={[buildPrimarySearch(), buildSecondarySearch(10000)]}>
      <SearchDialog searchPlaceholder="" />
    </MockedProvider>
  </AnalyticsContext.Provider>
);
