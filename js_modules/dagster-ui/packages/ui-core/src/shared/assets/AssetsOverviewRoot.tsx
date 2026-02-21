// eslint-disable-next-line no-restricted-imports
import {BreadcrumbProps} from '@blueprintjs/core';
import {Box} from '@dagster-io/ui-components';
import {observeEnabled} from '@shared/app/observeEnabled';
import {AssetGlobalLineageLink, AssetPageHeader} from '@shared/assets/AssetPageHeader';
import {useMemo} from 'react';
import {useHistory, useParams} from 'react-router-dom';

import {gql} from '../../apollo-client';
import {useTrackPageView} from '../../app/analytics';
import {displayNameForAssetKey} from '../../asset-graph/Utils';
import {AssetView} from '../../assets/AssetView';
import {AssetsCatalogTable} from '../../assets/AssetsCatalogTable';
import {assetDetailsPathForKey} from '../../assets/assetDetailsPathForKey';
import {AssetsCatalog} from '../../assets/catalog/AssetsCatalog';
import {AssetKey} from '../../assets/types';
import {useAssetViewParams} from '../../assets/useAssetViewParams';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {ReloadAllButton} from '../../workspace/ReloadAllButton';

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
              <ReloadAllButton label="Reload definitions" />
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
