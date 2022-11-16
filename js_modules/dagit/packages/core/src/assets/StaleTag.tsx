import {Colors, Box, BaseTag} from '@dagster-io/ui';
import React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';

export const StaleTag: React.FC<{liveData?: LiveDataForNode; onClick?: () => void}> = ({
  liveData,
  onClick,
}) =>
  liveData?.currentLogicalVersion !== liveData?.projectedLogicalVersion ? (
    <Box onClick={onClick}>
      <BaseTag
        fillColor={Colors.Yellow50}
        textColor={Colors.Yellow700}
        label="Stale"
        interactive={!!onClick}
      />
    </Box>
  ) : null;
