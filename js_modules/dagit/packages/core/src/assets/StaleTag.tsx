import {Colors, Box, BaseTag, Tooltip, Icon} from '@dagster-io/ui';
import React from 'react';

import {displayNameForAssetKey, LiveDataForNode} from '../asset-graph/Utils';
import {StaleStatus} from '../graphql/types';

export const isAssetMissing = (liveData?: LiveDataForNode) =>
  liveData && liveData.staleStatus === StaleStatus.MISSING;

export const isAssetStale = (liveData?: LiveDataForNode) =>
  liveData && liveData.staleStatus === StaleStatus.STALE;

const NO_CAUSES = 'No reasons available.';

export const StaleTag: React.FC<{liveData?: LiveDataForNode; onClick?: () => void}> = ({
  liveData,
  onClick,
}) => {
  if (!isAssetStale(liveData)) {
    return null;
  }
  const hasCauses = liveData?.staleCauses && liveData.staleCauses.length > 0;

  return (
    <Tooltip
      position="top"
      content={hasCauses ? <StaleCausesSummary causes={liveData.staleCauses} /> : NO_CAUSES}
    >
      <Box onClick={onClick}>
        <BaseTag
          fillColor={Colors.Yellow50}
          textColor={Colors.Yellow700}
          interactive={!!onClick}
          label={
            <Box flex={{gap: 4, alignItems: 'center'}}>
              Stale
              {hasCauses && <Icon name="info" size={12} color={Colors.Yellow700} />}
            </Box>
          }
        />
      </Box>
    </Tooltip>
  );
};

const MAX_DISPLAYED_REASONS = 4;

export const StaleCausesInfoDot: React.FC<{causes: LiveDataForNode['staleCauses']}> = ({
  causes,
}) => (
  <Tooltip
    position="top"
    content={causes && causes.length > 0 ? <StaleCausesSummary causes={causes} /> : NO_CAUSES}
  >
    <Icon name="info" size={12} color={Colors.Yellow700} />
  </Tooltip>
);

const StaleCausesSummary: React.FC<{causes: LiveDataForNode['staleCauses']}> = ({causes}) => (
  <Box>
    <strong>This asset is marked as stale:</strong>
    <ul style={{margin: 0, padding: '4px 12px'}}>
      {causes.slice(0, MAX_DISPLAYED_REASONS).map((cause, idx) => (
        <li key={idx}>
          [{displayNameForAssetKey(cause.key)}] {cause.reason}{' '}
          {cause.dependency ? `(${displayNameForAssetKey(cause.dependency)})` : ''}
        </li>
      ))}
      {causes.length > MAX_DISPLAYED_REASONS ? (
        <span style={{color: Colors.Gray400}}>{`and ${
          causes.length - MAX_DISPLAYED_REASONS
        } more...`}</span>
      ) : (
        ''
      )}
    </ul>
  </Box>
);
