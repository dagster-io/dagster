// eslint-disable-next-line no-restricted-imports
import {BreadcrumbProps} from '@blueprintjs/core';
import {Box} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {useHistory, useParams} from 'react-router-dom';
import {observeEnabled} from 'shared/app/observeEnabled.oss';
import {AssetGlobalLineageLink, AssetPageHeader} from 'shared/assets/AssetPageHeader.oss';

import {AssetView} from './AssetView';
import {AssetsCatalogTable} from './AssetsCatalogTable';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetsCatalog} from './catalog/AssetsCatalog';
import {AssetKey} from './types';
import {gql} from '../apollo-client';
import {useAssetViewParams} from './useAssetViewParams';
import {useTrackPageView} from '../app/analytics';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
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
  const [searchParams] = useAssetViewParams();

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

  useDocumentTitle(
    currentPath && currentPath.length
      ? `${documentTitlePrefix}: ${displayNameForAssetKey(assetKey)}`
      : documentTitlePrefix,
  );

  if (currentPath.length === 0 || searchParams.view === 'folder') {
    if (observeEnabled()) {
      return <AssetsCatalog />;
    }
    return (
      <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
        <AssetPageHeader
          view="catalog"
          assetKey={assetKey}
          headerBreadcrumbs={headerBreadcrumbs}
          right={
            <Box flex={{gap: 12, alignItems: 'center'}}>
              <AssetGlobalLineageLink />
              <ReloadAllButton label="重新加载定义" />
            </Box>
          }
        />

        <AssetsCatalogTable
          prefixPath={currentPath}
          setPrefixPath={(prefixPath) => history.push(assetDetailsPathForKey({path: prefixPath}))}
        />
      </Box>
    );
  }

  return (
    <AssetView
      assetKey={assetKey}
      headerBreadcrumbs={headerBreadcrumbs}
      writeAssetVisit={writeAssetVisit}
      currentPath={currentPath}
    />
  );
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
