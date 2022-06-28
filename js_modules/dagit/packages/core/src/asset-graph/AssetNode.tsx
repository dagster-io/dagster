import {gql} from '@apollo/client';
import {Colors, Icon, Tooltip, FontFamily, Box, CaptionMono, Spinner} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {withMiddleTruncation} from '../app/Util';
import {NodeHighlightColors} from '../graph/OpNode';
import {OpTags} from '../graph/OpTags';
import {linkToRunEvent, titleForRun} from '../runs/RunUtils';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {AssetComputeStatus} from '../types/globalTypes';
import {markdownToPlaintext} from '../ui/markdownToPlaintext';

import {displayNameForAssetKey, LiveDataForNode} from './Utils';
import {ASSET_NODE_ANNOTATIONS_MAX_WIDTH, ASSET_NODE_NAME_MAX_LENGTH} from './layout';
import {AssetNodeFragment} from './types/AssetNodeFragment';

const MISSING_LIVE_DATA = {
  unstartedRunIds: [],
  inProgressRunIds: [],
  runWhichFailedToMaterialize: null,
  lastMaterialization: null,
  computeStatus: AssetComputeStatus.NONE,
  stepKey: '',
};

export const AssetNode: React.FC<{
  definition: AssetNodeFragment;
  liveData?: LiveDataForNode;
  selected: boolean;
  inAssetCatalog?: boolean;
}> = React.memo(({definition, selected, liveData, inAssetCatalog}) => {
  const firstOp = definition.opNames.length ? definition.opNames[0] : null;
  const computeName = definition.graphName || definition.opNames[0] || null;

  // Used for linking to the run with this step highlighted. We only support highlighting
  // a single step, so just use the first one.
  const stepKey = firstOp || '';

  const displayName = withMiddleTruncation(displayNameForAssetKey(definition.assetKey), {
    maxLength: ASSET_NODE_NAME_MAX_LENGTH,
  });

  const {lastMaterialization, computeStatus} = liveData || MISSING_LIVE_DATA;

  return (
    <AssetNodeContainer $selected={selected}>
      <AssetNodeBox $selected={selected}>
        <Name>
          <span style={{marginTop: 1}}>
            <Icon name="asset" />
          </span>
          <div style={{overflow: 'hidden', textOverflow: 'ellipsis', marginTop: -1}}>
            {displayName}
          </div>
          <div style={{flex: 1}} />
          <div style={{maxWidth: ASSET_NODE_ANNOTATIONS_MAX_WIDTH}}>
            <ComputeStatusNotice computeStatus={computeStatus} />
          </div>
        </Name>
        {definition.description && !inAssetCatalog && (
          <Description>{markdownToPlaintext(definition.description).split('\n')[0]}</Description>
        )}
        {computeName && displayName !== computeName && (
          <Description>
            <Box
              flex={{gap: 4, alignItems: 'flex-end'}}
              style={{marginLeft: -2, overflow: 'hidden'}}
            >
              <Icon name={definition.graphName ? 'job' : 'op'} size={16} />
              <div style={{minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis'}}>
                {computeName}
              </div>
            </Box>
          </Description>
        )}

        <Stats>
          {lastMaterialization ? (
            <StatsRow>
              <span>Materialized</span>
              <CaptionMono>
                <AssetRunLink
                  runId={lastMaterialization.runId}
                  event={{stepKey, timestamp: lastMaterialization.timestamp}}
                >
                  <TimestampDisplay
                    timestamp={Number(lastMaterialization.timestamp) / 1000}
                    timeFormat={{showSeconds: false, showTimezone: false}}
                  />
                </AssetRunLink>
              </CaptionMono>
            </StatsRow>
          ) : (
            <>
              <StatsRow>
                <span>Materialized</span>
                <span>–</span>
              </StatsRow>
            </>
          )}
          <StatsRow>
            <span>Latest Run</span>
            <CaptionMono>
              <AssetLatestRunWithNotices liveData={liveData} />
            </CaptionMono>
          </StatsRow>
        </Stats>
        {definition.computeKind && (
          <OpTags
            minified={false}
            style={{right: -2, paddingTop: 5}}
            tags={[
              {
                label: definition.computeKind,
                onClick: () => {
                  window.requestAnimationFrame(() =>
                    document.dispatchEvent(new Event('show-kind-info')),
                  );
                },
              },
            ]}
          />
        )}
      </AssetNodeBox>
    </AssetNodeContainer>
  );
}, isEqual);

export const AssetNodeMinimal: React.FC<{
  selected: boolean;
  definition: AssetNodeFragment;
}> = ({selected, definition}) => {
  return (
    <MinimalAssetNodeContainer $selected={selected}>
      <MinimalAssetNodeBox $selected={selected}>
        <MinimalName style={{fontSize: 28}}>
          {withMiddleTruncation(displayNameForAssetKey(definition.assetKey), {maxLength: 17})}
        </MinimalName>
      </MinimalAssetNodeBox>
    </MinimalAssetNodeContainer>
  );
};

export const AssetRunLink: React.FC<{
  runId: string;
  event?: Parameters<typeof linkToRunEvent>[1];
}> = ({runId, children, event}) => (
  <Link
    to={event ? linkToRunEvent({runId}, event) : `/instance/runs/${runId}`}
    target="_blank"
    rel="noreferrer"
  >
    {children || titleForRun({runId})}
  </Link>
);

export const ASSET_NODE_LIVE_FRAGMENT = gql`
  fragment AssetNodeLiveFragment on AssetNode {
    id
    opNames
    repository {
      id
    }
    assetKey {
      path
    }
    assetMaterializations(limit: 1) {
      timestamp
      runId
    }
  }
`;

// Note: This fragment should only contain fields that are needed for
// useAssetGraphData and the Asset DAG. Some pages of Dagit request this
// fragment for every AssetNode on the instance. Add fields with care!
//
export const ASSET_NODE_FRAGMENT = gql`
  fragment AssetNodeFragment on AssetNode {
    id
    graphName
    jobNames
    opNames
    description
    computeKind
    assetKey {
      path
    }
  }
`;

const BoxColors = {
  Divider: 'rgba(219, 219, 244, 1)',
  Description: 'rgba(245, 245, 250, 1)',
  Stats: 'rgba(236, 236, 248, 1)',
};

const AssetNodeContainer = styled.div<{$selected: boolean}>`
  outline: ${(p) => (p.$selected ? `2px dashed ${NodeHighlightColors.Border}` : 'none')};
  border-radius: 6px;
  outline-offset: -1px;
  background: ${(p) => (p.$selected ? NodeHighlightColors.Background : 'white')};
  inset: 0;
  padding: 4px;
  margin-top: 10px;
  margin-right: 4px;
  margin-left: 4px;
  margin-bottom: 2px;
`;

const AssetNodeBox = styled.div<{$selected: boolean}>`
  border: 2px solid ${(p) => (p.$selected ? Colors.Blue500 : Colors.Blue200)};
  background: ${BoxColors.Stats};
  border-radius: 5px;
  position: relative;
  &:hover {
    box-shadow: ${Colors.Blue200} inset 0px 0px 0px 1px, rgba(0, 0, 0, 0.12) 0px 2px 12px 0px;
  }
`;

const Name = styled.div`
  /** Keep in sync with DISPLAY_NAME_PX_PER_CHAR */
  display: flex;
  padding: 4px 6px;
  background: ${Colors.White};
  font-family: ${FontFamily.monospace};
  border-top-left-radius: 5px;
  border-top-right-radius: 5px;
  font-weight: 600;
  gap: 4px;
`;

const MinimalAssetNodeContainer = styled(AssetNodeContainer)`
  position: absolute;
  border-radius: 12px;
  outline-offset: 2px;
  outline-width: 4px;
`;

const MinimalAssetNodeBox = styled(AssetNodeBox)`
  background: ${Colors.White};
  border: 4px solid ${Colors.Blue200};
  border-radius: 10px;
  position: absolute;
  inset: 4px;
`;

const MinimalName = styled(Name)`
  font-weight: 600;
  white-space: nowrap;
  position: absolute;
  background: none;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
`;

const Description = styled.div`
  background: ${BoxColors.Description};
  padding: 4px 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-top: 1px solid ${BoxColors.Divider};
  font-size: 12px;
`;

const Stats = styled.div`
  background: ${BoxColors.Stats};
  padding: 4px 8px;
  border-top: 1px solid ${BoxColors.Divider};
  font-size: 12px;
  line-height: 20px;
`;

const StatsRow = styled.div`
  display: flex;
  justify-content: space-between;
  min-height: 18px;
  & > span {
    color: ${Colors.Gray600};
  }
`;

const UpstreamNotice = styled.div`
  background: ${Colors.Yellow200};
  color: ${Colors.Yellow700};
  line-height: 10px;
  font-size: 11px;
  text-align: right;
  margin-top: -4px;
  margin-bottom: -4px;
  padding: 2.5px 5px;
  margin-right: -6px;
  border-top-right-radius: 3px;
`;

export const ComputeStatusNotice: React.FC<{computeStatus: AssetComputeStatus}> = ({
  computeStatus,
}) =>
  computeStatus === AssetComputeStatus.OUT_OF_DATE ? (
    <UpstreamNotice>
      upstream
      <br />
      changed
    </UpstreamNotice>
  ) : null;

export const AssetLatestRunWithNotices: React.FC<{
  liveData?: LiveDataForNode;
}> = ({liveData}) => {
  const {
    lastMaterialization,
    unstartedRunIds,
    inProgressRunIds,
    runWhichFailedToMaterialize,
    stepKey,
  } = liveData || MISSING_LIVE_DATA;

  return inProgressRunIds?.length > 0 ? (
    <Box flex={{gap: 4, alignItems: 'center'}}>
      <Tooltip content="A run is currently rematerializing this asset.">
        <Spinner purpose="body-text" />
      </Tooltip>
      <AssetRunLink runId={inProgressRunIds[0]} />
    </Box>
  ) : unstartedRunIds?.length > 0 ? (
    <Box flex={{gap: 4, alignItems: 'center'}}>
      <Tooltip content="A run has started that will rematerialize this asset soon.">
        <Spinner purpose="body-text" stopped />
      </Tooltip>
      <AssetRunLink runId={unstartedRunIds[0]} />
    </Box>
  ) : runWhichFailedToMaterialize?.__typename === 'Run' ? (
    <Box flex={{gap: 4, alignItems: 'center'}}>
      <Tooltip
        content={`Run ${titleForRun({
          runId: runWhichFailedToMaterialize.id,
        })} failed to materialize this asset`}
      >
        <Icon name="warning" color={Colors.Red500} />
      </Tooltip>
      <AssetRunLink runId={runWhichFailedToMaterialize.id} />
    </Box>
  ) : lastMaterialization ? (
    <AssetRunLink
      runId={lastMaterialization.runId}
      event={{stepKey, timestamp: lastMaterialization.timestamp}}
    />
  ) : (
    <span>–</span>
  );
};
