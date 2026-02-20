import {Box, ButtonGroup} from '@dagster-io/ui-components';
import {CreateCatalogViewButton} from '@shared/assets/CreateCatalogViewButton';
import {useFavoriteAssets} from '@shared/assets/useFavoriteAssets';
import * as React from 'react';
import {useEffect, useMemo, useState} from 'react';
import {useRouteMatch} from 'react-router-dom';
import {useSetRecoilState} from 'recoil';

import {AssetTable} from './AssetTable';
import {ASSET_TABLE_DEFINITION_FRAGMENT, ASSET_TABLE_FRAGMENT} from './AssetTableFragment';
import {AssetsEmptyState} from './AssetsEmptyState';
import {AssetTableFragment} from './types/AssetTableFragment.types';
import {useAllAssets} from './useAllAssets';
import {AssetViewType, useAssetView} from './useAssetView';
import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useRefreshAtInterval} from '../app/QueryRefresh';
import {currentPageAtom} from '../app/analytics';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {useAssetSelectionInput} from '../asset-selection/input/useAssetSelectionInput';
import {AssetGroupSelector} from '../graphql/types';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {SyntaxError} from '../selection/CustomErrorListener';
import {LoadingSpinner} from '../ui/Loading';

export {useAllAssets} from './useAllAssets';

type Asset = AssetTableFragment;
const emptyArray: string[] = [];

interface AssetCatalogTableProps {
  prefixPath: string[];
  setPrefixPath: (prefixPath: string[]) => void;
  groupSelector?: AssetGroupSelector;
}

export const AssetsCatalogTable = ({
  prefixPath,
  setPrefixPath,
  groupSelector,
}: AssetCatalogTableProps) => {
  const setCurrentPage = useSetRecoilState(currentPageAtom);
  const {path} = useRouteMatch();
  useEffect(() => {
    setCurrentPage(({specificPath}) => ({specificPath, path: `${path}?view=AssetCatalogTable`}));
  }, [path, setCurrentPage]);

  const [view, setView] = useAssetView();

  const {assets, loading: assetsLoading, query, error} = useAllAssets({groupSelector});

  const {favorites, loading: favoritesLoading} = useFavoriteAssets();
  const penultimateAssets = useMemo(() => {
    if (!favorites) {
      return assets ?? [];
    }
    return (assets ?? []).filter((asset) => favorites.has(tokenForAssetKey(asset.key)));
  }, [favorites, assets]);

  const [errorState, setErrorState] = useState<SyntaxError[]>([]);
  const {filterInput, filtered, loading, assetSelection, setAssetSelection} =
    useAssetSelectionInput({
      assets: penultimateAssets,
      assetsLoading: !assets || assetsLoading || favoritesLoading,
      onErrorStateChange: (errors) => {
        if (errors !== errorState) {
          setErrorState(errors);
        }
      },
    });

  useBlockTraceUntilTrue('useAllAssets', !loading);

  const {displayPathForAsset, displayed} = useMemo(
    () =>
      view === 'flat'
        ? buildFlatProps(filtered as AssetTableFragment[], prefixPath)
        : buildNamespaceProps(filtered as AssetTableFragment[], prefixPath),
    [filtered, prefixPath, view],
  );

  const refreshState = useRefreshAtInterval<any>({
    refresh: query,
    intervalMs: 4 * FIFTEEN_SECONDS,
    leading: true,
  });

  React.useEffect(() => {
    if (view !== 'directory' && prefixPath.length) {
      setView('directory');
    }
  }, [view, setView, prefixPath]);

  if (error) {
    return <PythonErrorInfo error={error} />;
  }

  if (!assets) {
    return <LoadingSpinner purpose="page" />;
  }

  if (!assets.length) {
    return (
      <Box padding={{vertical: 64}}>
        <AssetsEmptyState prefixPath={prefixPath} />
      </Box>
    );
  }

  return (
    <AssetTable
      view={view}
      assets={displayed}
      isLoading={loading}
      errorState={errorState}
      actionBarComponents={
        <Box flex={{gap: 12, alignItems: 'flex-start'}}>
          <ButtonGroup<AssetViewType>
            activeItems={new Set([view])}
            buttons={[
              {id: 'flat', icon: 'view_list', tooltip: 'List view'},
              {id: 'directory', icon: 'folder', tooltip: 'Folder view'},
            ]}
            onClick={(view) => {
              setView(view);
              if (view === 'flat' && prefixPath.length) {
                setPrefixPath([]);
              }
            }}
          />
          {filterInput}
          <CreateCatalogViewButton />
        </Box>
      }
      refreshState={refreshState}
      prefixPath={prefixPath || emptyArray}
      assetSelection={assetSelection}
      displayPathForAsset={displayPathForAsset}
      onChangeAssetSelection={setAssetSelection}
    />
  );
};

export const ASSET_CATALOG_TABLE_QUERY = gql`
  query AssetCatalogTableQuery($cursor: String, $limit: Int!) {
    assetsOrError(cursor: $cursor, limit: $limit) {
      ... on AssetConnection {
        nodes {
          id
          ...AssetTableFragment
        }
        cursor
      }
      ...PythonErrorFragment
    }
  }

  ${ASSET_TABLE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const ASSET_CATALOG_GROUP_TABLE_QUERY = gql`
  query AssetCatalogGroupTableQuery($group: AssetGroupSelector) {
    assetNodes(group: $group) {
      id
      ...AssetCatalogGroupTableNode
    }
  }

  fragment AssetCatalogGroupTableNode on AssetNode {
    id
    assetKey {
      path
    }
    ...AssetTableDefinitionFragment
  }

  ${ASSET_TABLE_DEFINITION_FRAGMENT}
`;

function buildFlatProps(assets: Asset[], _: string[]) {
  return {
    displayed: assets,
    displayPathForAsset: (asset: Asset) => asset.key.path,
  };
}

function buildNamespaceProps(assets: Asset[], prefixPath: string[]) {
  // Return all assets matching prefixPath - the AssetTable component will later
  // group them by namespace

  const namespaceForAsset = (asset: Asset) => {
    return asset.key.path.slice(prefixPath.length, prefixPath.length + 1);
  };

  const assetsWithPathPrefix = assets.filter((asset) =>
    prefixPath.every((part, index) => part === asset.key.path[index]),
  );

  return {
    displayPathForAsset: namespaceForAsset,
    displayed: assetsWithPathPrefix,
  };
}
