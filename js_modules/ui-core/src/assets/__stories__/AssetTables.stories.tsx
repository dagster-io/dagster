import {MockedProvider} from '@apollo/client/testing';

import {StorybookProvider} from '../../testing/StorybookProvider';
import {AssetsCatalogTable} from '../AssetsCatalogTable';
import {
  AssetCatalogGroupTableMock,
  AssetCatalogTableMock,
  SingleAssetQueryLastRunFailed,
  SingleAssetQueryMaterializedStaleAndLate,
  SingleAssetQueryMaterializedWithLatestRun,
  SingleAssetQueryTrafficDashboard,
} from '../__fixtures__/AssetTables.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Assets/AssetsCatalogTable',
  component: AssetsCatalogTable,
};

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
