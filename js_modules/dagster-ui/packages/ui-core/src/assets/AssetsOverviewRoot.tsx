import {gql, useQuery} from '@apollo/client';
// eslint-disable-next-line no-restricted-imports
import {BreadcrumbProps} from '@blueprintjs/core';
import {Box, Colors, Page, Spinner} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {AssetGlobalLineageLink, AssetPageHeader} from './AssetPageHeader';
import {AssetView} from './AssetView';
import {AssetsCatalogTable} from './AssetsCatalogTable';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetKey} from './types';
import {
  AssetsOverviewRootQuery,
  AssetsOverviewRootQueryVariables,
} from './types/AssetsOverviewRoot.types';
import {useTrackPageView} from '../app/analytics';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {usePageLoadTrace} from '../performance';
import {ReloadAllButton} from '../workspace/ReloadAllButton';

export const AssetsOverviewRoot = ({
  writeAssetVisit,
  headerBreadcrumbs,
  documentTitlePrefix,
}: {
  writeAssetVisit?: (assetKey: AssetKey) => void;
  headerBreadcrumbs: BreadcrumbProps[];
  documentTitlePrefix: string;
}) => {
  useTrackPageView();

  const params = useParams();
  const history = useHistory();

  const currentPathStr = (params as any)['0'];
  const currentPath: string[] = useMemo(
    () =>
      (currentPathStr || '')
        .split('/')
        .filter((x: string) => x)
        .map(decodeURIComponent),
    [currentPathStr],
  );
  const assetKey = useMemo(() => ({path: currentPath}), [currentPath]);

  const queryResult = useQuery<AssetsOverviewRootQuery, AssetsOverviewRootQueryVariables>(
    ASSETS_OVERVIEW_ROOT_QUERY,
    {
      skip: currentPath.length === 0,
      variables: {assetKey},
    },
  );

  useDocumentTitle(
    currentPath && currentPath.length
      ? `${documentTitlePrefix}: ${displayNameForAssetKey(assetKey)}`
      : documentTitlePrefix,
  );

  const trace = usePageLoadTrace(
    currentPath && currentPath.length === 0 ? 'AssetsOverviewRoot' : 'AssetCatalogAssetView',
  );

  React.useEffect(() => {
    // If the asset exists, add it to the recently visited list
    if (
      currentPath &&
      currentPath.length &&
      queryResult.loading === false &&
      queryResult.data?.assetOrError.__typename === 'Asset' &&
      writeAssetVisit
    ) {
      writeAssetVisit({path: currentPath});
    }
  }, [currentPath, queryResult, writeAssetVisit]);

  if (queryResult.loading) {
    return (
      <Page>
        <AssetPageHeader assetKey={assetKey} headerBreadcrumbs={headerBreadcrumbs} />
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
          assetKey={assetKey}
          headerBreadcrumbs={headerBreadcrumbs}
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

  return <AssetView assetKey={assetKey} trace={trace} headerBreadcrumbs={headerBreadcrumbs} />;
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default AssetsOverviewRoot;

export const ASSETS_OVERVIEW_ROOT_QUERY = gql`
  query AssetsOverviewRootQuery($assetKey: AssetKeyInput!) {
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
