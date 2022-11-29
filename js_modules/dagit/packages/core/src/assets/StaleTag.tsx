import {Colors, Box, BaseTag} from '@dagster-io/ui';
import React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';

export const isAssetMissing = (liveData?: LiveDataForNode) =>
  liveData && liveData.currentLogicalVersion === null;

export const isAssetStale = (liveData?: LiveDataForNode) =>
  liveData &&
  liveData.currentLogicalVersion !== null &&
  liveData.currentLogicalVersion !== 'INITIAL' &&
  liveData.currentLogicalVersion !== liveData.projectedLogicalVersion;

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
