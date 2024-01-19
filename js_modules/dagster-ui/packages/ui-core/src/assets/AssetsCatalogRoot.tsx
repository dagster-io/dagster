import {gql, useQuery} from '@apollo/client';
import {Box, Page, Spinner, Colors} from '@dagster-io/ui-components';
import * as React from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {useTrackPageView} from '../app/analytics';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useStartTrace} from '../performance';
import {ReloadAllButton} from '../workspace/ReloadAllButton';

import {AssetGlobalLineageLink, AssetPageHeader} from './AssetPageHeader';
import {AssetView} from './AssetView';
import {AssetsCatalogTable} from './AssetsCatalogTable';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {
  AssetsCatalogRootQuery,
  AssetsCatalogRootQueryVariables,
} from './types/AssetsCatalogRoot.types';

export const AssetsCatalogRoot = () => {
  useTrackPageView();

  const params = useParams();
  const history = useHistory();
  const currentPath: string[] = ((params as any)['0'] || '')
    .split('/')
    .filter((x: string) => x)
    .map(decodeURIComponent);

  const queryResult = useQuery<AssetsCatalogRootQuery, AssetsCatalogRootQueryVariables>(
    ASSETS_CATALOG_ROOT_QUERY,
    {
      skip: currentPath.length === 0,
      variables: {assetKey: {path: currentPath}},
    },
  );

  useDocumentTitle(
    currentPath && currentPath.length
      ? `Assets: ${displayNameForAssetKey({path: currentPath})}`
      : 'Assets',
  );

  const trace = useStartTrace(
    currentPath && currentPath.length === 0 ? 'AssetsCatalogRoot' : 'AssetCatalogAssetView',
  );

  if (queryResult.loading) {
    return (
      <Page>
        <AssetPageHeader assetKey={{path: currentPath}} />
        <Box flex={{direction: 'row', justifyContent: 'center'}} style={{paddingTop: '100px'}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
            <Spinner purpose="body-text" />
            <div style={{color: Colors.textLight()}}>Loading assets…</div>
          </Box>
        </Box>
      </Page>
    );
  }

  if (
    currentPath.length === 0 ||
    queryResult.data?.assetOrError.__typename === 'AssetNotFoundError'
  ) {
    return (
      <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
        <AssetPageHeader
          assetKey={{path: currentPath}}
          right={
            <Box flex={{gap: 12, alignItems: 'center'}}>
              <AssetGlobalLineageLink />
              <ReloadAllButton label="Reload definitions" />
            </Box>
          }
        />
        <AssetsCatalogTable
          prefixPath={currentPath}
          setPrefixPath={(prefixPath) => history.push(assetDetailsPathForKey({path: prefixPath}))}
          trace={trace}
        />
      </Box>
    );
  }

  return <AssetView assetKey={{path: currentPath}} trace={trace} />;
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default AssetsCatalogRoot;

const ASSETS_CATALOG_ROOT_QUERY = gql`
  query AssetsCatalogRootQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }
      }
    }
  }
`;
