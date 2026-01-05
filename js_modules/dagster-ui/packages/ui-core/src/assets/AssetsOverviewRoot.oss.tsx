// eslint-disable-next-line no-restricted-imports
import {BreadcrumbProps} from '@blueprintjs/core';
import {useMemo} from 'react';
import {useParams} from 'react-router-dom';

import {AssetView} from './AssetView';
import {AssetsCatalog} from './catalog/AssetsCatalog';
import {AssetKey} from './types';
import {gql} from '../apollo-client';
import {useAssetViewParams} from './useAssetViewParams';
import {useTrackPageView} from '../app/analytics';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

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
    return <AssetsCatalog />;
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
