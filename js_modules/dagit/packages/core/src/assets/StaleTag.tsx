import {Colors, Box, BaseTag} from '@dagster-io/ui';
import React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';
import {StaleStatus} from '../graphql/types';

export const isAssetMissing = (liveData?: LiveDataForNode) =>
  liveData && liveData.staleStatus === StaleStatus.MISSING;

export const isAssetStale = (liveData?: LiveDataForNode) =>
  liveData && liveData.staleStatus === StaleStatus.STALE;

export const StaleTag: React.FC<{liveData?: LiveDataForNode; onClick?: () => void}> = ({
  liveData,
  onClick,
}) =>
  isAssetStale(liveData) ? (
    <Box onClick={onClick}>
      <BaseTag
        fillColor={Colors.Yellow50}
        textColor={Colors.Yellow700}
        label="Stale"
        interactive={!!onClick}
      />
    </Box>
  ) : null;
