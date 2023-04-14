import {MockedProvider} from '@apollo/client/testing';
import React from 'react';

import {StorybookProvider} from '../../testing/StorybookProvider';
import {AssetsCatalogTable} from '../AssetsCatalogTable';
import {
  AssetCatalogGroupTableMock,
  AssetCatalogTableMock,
  SingleAssetQueryLastRunFailed,
  SingleAssetQueryMaterializedStaleAndLate,
  SingleAssetQueryMaterializedWithLatestRun,
  SingleAssetQueryTrafficDashboard,
} from '../__fixtures__/AssetsCatalogTable.fixtures';

// eslint-disable-next-line import/no-default-export
export default {component: AssetsCatalogTable};

const MOCKS = [
  AssetCatalogTableMock,
  AssetCatalogGroupTableMock,
  SingleAssetQueryTrafficDashboard,
  SingleAssetQueryMaterializedWithLatestRun,
  SingleAssetQueryMaterializedStaleAndLate,
  SingleAssetQueryLastRunFailed,
];

export const NoPrefixPath = () => {
  return (
    <StorybookProvider routerProps={{initialEntries: ['/']}}>
      <MockedProvider mocks={MOCKS}>
        <AssetsCatalogTable prefixPath={[]} setPrefixPath={() => {}} />
      </MockedProvider>
    </StorybookProvider>
  );
};

export const WithinAssetPath = () => {
  return (
    <StorybookProvider routerProps={{initialEntries: ['/']}}>
      <MockedProvider mocks={MOCKS}>
        <AssetsCatalogTable prefixPath={['dashboards']} setPrefixPath={() => {}} />
      </MockedProvider>
    </StorybookProvider>
  );
};
