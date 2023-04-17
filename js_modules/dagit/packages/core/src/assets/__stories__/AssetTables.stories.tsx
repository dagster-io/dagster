import {MockedProvider} from '@apollo/client/testing';
import {Box} from '@dagster-io/ui';
import React from 'react';

import {StorybookProvider} from '../../testing/StorybookProvider';
import {VirtualizedRepoAssetTable} from '../../workspace/VirtualizedRepoAssetTable';
import {AssetsCatalogTable} from '../AssetsCatalogTable';
import {
  AssetCatalogGroupTableMock,
  AssetCatalogTableMock,
  AssetCatalogTableMockAssets,
  SingleAssetQueryLastRunFailed,
  SingleAssetQueryMaterializedStaleAndLate,
  SingleAssetQueryMaterializedWithLatestRun,
  SingleAssetQueryTrafficDashboard,
} from '../__fixtures__/AssetTables.fixtures';

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

export const GlobalCatalogNoPrefix = () => {
  return (
    <StorybookProvider routerProps={{initialEntries: ['/']}}>
      <MockedProvider mocks={MOCKS}>
        <AssetsCatalogTable prefixPath={[]} setPrefixPath={() => {}} />
      </MockedProvider>
    </StorybookProvider>
  );
};

export const GlobalCatalogWithPrefix = () => {
  return (
    <StorybookProvider routerProps={{initialEntries: ['/']}}>
      <MockedProvider mocks={MOCKS}>
        <AssetsCatalogTable prefixPath={['dashboards']} setPrefixPath={() => {}} />
      </MockedProvider>
    </StorybookProvider>
  );
};

export const RepoAssets = () => {
  return (
    <StorybookProvider routerProps={{initialEntries: ['/']}}>
      <MockedProvider mocks={MOCKS}>
        <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
          <VirtualizedRepoAssetTable
            repoAddress={{name: 'repo', location: 'test.py'}}
            assets={AssetCatalogTableMockAssets.filter((a) => !!a.definition).map((a) => ({
              id: a.id,
              assetKey: a.key,
              groupName: a.definition!.groupName,
            }))}
          />
        </Box>
      </MockedProvider>
    </StorybookProvider>
  );
};
