import {Colors, Box, BaseTag, Tooltip, Icon, Body} from '@dagster-io/ui';
import groupBy from 'lodash/groupBy';
import isEqual from 'lodash/isEqual';
import React from 'react';

import {displayNameForAssetKey, LiveDataForNode} from '../asset-graph/Utils';
import {AssetKeyInput, StaleCauseCategory, StaleStatus} from '../graphql/types';

export const isAssetMissing = (liveData?: LiveDataForNode) =>
  liveData && liveData.staleStatus === StaleStatus.MISSING;

export const isAssetStale = (liveData?: LiveDataForNode) =>
  liveData && liveData.staleStatus === StaleStatus.STALE;

const NO_CAUSES = 'No reasons available.';

const LABELS = {
  self: {
    [StaleCauseCategory.CODE]: 'Code version',
    [StaleCauseCategory.DATA]: 'Data version',
    [StaleCauseCategory.DEPENDENCIES]: 'Dependencies',
  },
  upstream: {
    [StaleCauseCategory.CODE]: 'Upstream code version',
    [StaleCauseCategory.DATA]: 'Upstream data version',
    [StaleCauseCategory.DEPENDENCIES]: 'Upstream dependencies',
  },
};

export const StaleReasonsLabel: React.FC<{
  assetKey: AssetKeyInput;
  include: 'all' | 'upstream' | 'self';
  liveData?: LiveDataForNode;
  onClick?: () => void;
}> = ({liveData, include, assetKey, onClick}) => {
  if (!isAssetStale(liveData) || !liveData?.staleCauses.length) {
    return null;
  }

  return (
    <Body color={Colors.Yellow700}>
      <Tooltip position="top" content={<StaleCausesSummary causes={liveData.staleCauses} />}>
        <Box onClick={onClick} flex={{gap: 4}}>
          {Object.keys(groupedCauses(assetKey, include, liveData)).join(', ')}
        </Box>
      </Tooltip>
    </Body>
  );
};

export const StaleReasonsTags: React.FC<{
  assetKey: AssetKeyInput;
  include: 'all' | 'upstream' | 'self';
  liveData?: LiveDataForNode;
  onClick?: () => void;
}> = ({liveData, include, assetKey, onClick}) => {
  if (!isAssetStale(liveData) || !liveData?.staleCauses.length) {
    return null;
  }

  return (
    <>
      {Object.entries(groupedCauses(assetKey, include, liveData)).map(([label, causes]) => (
        <Tooltip key={label} position="top" content={<StaleCausesSummary causes={causes} />}>
          <Box onClick={onClick} flex={{gap: 4}}>
            <BaseTag
              fillColor={Colors.Yellow50}
              textColor={Colors.Yellow700}
              interactive={!!onClick}
              icon={<Icon name="changes_present" color={Colors.Yellow700} />}
              label={label}
            />
          </Box>
        </Tooltip>
      ))}
    </>
  );
};

const MAX_DISPLAYED_REASONS = 4;

function groupedCauses(
  assetKey: AssetKeyInput,
  include: 'all' | 'upstream' | 'self',
  liveData?: LiveDataForNode,
) {
  const all = (liveData?.staleCauses || [])
    .map((cause) => {
      const target = isEqual(assetKey.path, cause.key.path) ? 'self' : 'upstream';
      return {...cause, target, label: LABELS[target][cause.category]};
    })
    .filter((cause) => include === 'all' || include === cause.target);

  return groupBy(all, (cause) => cause.label);
}

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
