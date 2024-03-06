import {render, screen} from '@testing-library/react';
import {MockedProvider} from '@apollo/client/testing';
import {
  AutoMaterializeDecisionType,
  AutoMaterializePolicyType,
  buildAsset,
  buildAssetKey,
  buildAssetNode,
  buildAutoMaterializePolicy,
  buildAutoMaterializeRule,
  buildCompositeConfigType,
  buildConfigTypeField,
  buildDimensionPartitionKeys,
  buildPartitionDefinition,
  buildRepository,
  buildRepositoryLocation,
} from '../../graphql/types';
import {AssetFeatureProvider} from '../AssetFeatureContext';
import {buildAssetTabs} from '../AssetTabs';
import AssetsCatalogRoot, {ASSETS_CATALOG_ROOT_QUERY} from '../AssetsCatalogRoot';
import {fetchRecentlyVisitedAssetsFromLocalStorage} from '../RecentlyVisitedAssetsStorage';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';
import {MemoryRouter} from 'react-router-dom';
import Router from 'react-router-dom';
import {buildQueryMock} from '../../testing/mocking';
import {
  AssetsCatalogRootQuery,
  AssetsCatalogRootQueryVariables,
} from '../types/AssetsCatalogRoot.types';
import {AssetGraphQueryVariables} from '../../asset-graph/types/useAssetGraphData.types';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: jest.fn(),
}));

describe('buildAssetTabs', () => {
  it('shows all tabs', () => {
    // const location = {
    //   ...window.location,
    //   pathname: '/assets/asset_1',
    // };
    // Object.defineProperty(window, 'location', {
    //   writable: true,
    //   value: location,
    // });
    // window.history.pushState({}, 'Test Title', '/assets/asset_1');
    jest.spyOn(Router, 'useParams').mockReturnValue({0: 'asset_1'});

    render(
      <MockedProvider
        mocks={[
          buildQueryMock<AssetsCatalogRootQuery, AssetsCatalogRootQueryVariables>({
            query: ASSETS_CATALOG_ROOT_QUERY,
            variables: {
              assetKey: {path: ['asset_1']},
            },
            data: {
              assetOrError: buildAsset({
                key: buildAssetKey({path: ['asset_1']}),
              }),
            },
          }),
        ]}
      >
        <MemoryRouter initialEntries={['/assets/asset_1']}>
          <AssetsCatalogRoot />
        </MemoryRouter>
      </MockedProvider>,
    );

    console.log('alsdkjaslkdj');

    expect(fetchRecentlyVisitedAssetsFromLocalStorage()).toEqual([]);
    expect(false).toEqual(true);
  });
});
