import {Box, Button, MiddleTruncate, Subtitle2} from '@dagster-io/ui-components';
import React, {useState} from 'react';
import {Link} from 'react-router-dom';

import {NoValue} from './Common';
import {displayNameForAssetKey, sortAssetKeys, tokenForAssetKey} from '../../asset-graph/Utils';
import {StatusDot} from '../../asset-graph/sidebar/StatusDot';
import {WorkspaceAssetFragment} from '../../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {DependsOnSelfBanner} from '../DependsOnSelfBanner';
import {assetDetailsPathForKey} from '../assetDetailsPathForKey';

export const LineageSection = ({
  dependsOnSelf,
  upstream,
  downstream,
}: {
  upstream: WorkspaceAssetFragment[] | null;
  downstream: WorkspaceAssetFragment[] | null;
  dependsOnSelf: boolean;
}) => {
  return (
    <>
      {dependsOnSelf && (
        <Box padding={{bottom: 12}}>
          <DependsOnSelfBanner />
        </Box>
      )}

      <Box flex={{direction: 'row'}}>
        <Box flex={{direction: 'column', gap: 6}} style={{width: '50%'}}>
          <Subtitle2>Upstream assets</Subtitle2>
          {upstream?.length ? (
            <AssetLinksWithStatus assets={upstream} />
          ) : (
            <Box>
              <NoValue />
            </Box>
          )}
        </Box>
        <Box flex={{direction: 'column', gap: 6}} style={{width: '50%'}}>
          <Subtitle2>Downstream assets</Subtitle2>
          {downstream?.length ? (
            <AssetLinksWithStatus assets={downstream} />
          ) : (
            <Box>
              <NoValue />
            </Box>
          )}
        </Box>
      </Box>
    </>
  );
};

const AssetLinksWithStatus = ({
  assets,
  displayedByDefault = 20,
}: {
  assets: WorkspaceAssetFragment[];
  displayedByDefault?: number;
}) => {
  const [displayedCount, setDisplayedCount] = useState(displayedByDefault);

  const displayed = React.useMemo(
    () => assets.sort((a, b) => sortAssetKeys(a.assetKey, b.assetKey)).slice(0, displayedCount),
    [assets, displayedCount],
  );

  return (
    <Box flex={{direction: 'column', gap: 6}}>
      {displayed.map((asset) => (
        <Link to={assetDetailsPathForKey(asset.assetKey)} key={tokenForAssetKey(asset.assetKey)}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'auto minmax(0, 1fr)',
              gap: '6px',
              alignItems: 'center',
            }}
          >
            <StatusDot node={{assetKey: asset.assetKey, definition: asset}} />
            <MiddleTruncate text={displayNameForAssetKey(asset.assetKey)} />
          </div>
        </Link>
      ))}
      <Box>
        {displayed.length < assets.length ? (
          <Button onClick={() => setDisplayedCount(Number.MAX_SAFE_INTEGER)}>
            Show {assets.length - displayed.length} more
          </Button>
        ) : displayed.length > displayedByDefault ? (
          <Button onClick={() => setDisplayedCount(displayedByDefault)}>Show less</Button>
        ) : undefined}
      </Box>
    </Box>
  );
};
