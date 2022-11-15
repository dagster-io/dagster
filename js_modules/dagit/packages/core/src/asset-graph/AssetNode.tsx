import {gql} from '@apollo/client';
import {
  Colors,
  Icon,
  Tooltip,
  FontFamily,
  Box,
  CaptionMono,
  Spinner,
  Caption,
  Tag,
} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import moment from 'moment-timezone';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {withMiddleTruncation} from '../app/Util';
import {NodeHighlightColors} from '../graph/OpNode';
import {OpTags} from '../graph/OpTags';
import {RunStatusIndicator} from '../runs/RunStatusDots';
import {linkToRunEvent, titleForRun} from '../runs/RunUtils';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {humanCronString} from '../schedules/humanCronString';
import {AssetComputeStatus} from '../types/globalTypes';
import {markdownToPlaintext} from '../ui/markdownToPlaintext';

import {LiveDataForNode} from './Utils';
import {ASSET_NODE_ANNOTATIONS_MAX_WIDTH, ASSET_NODE_NAME_MAX_LENGTH} from './layout';
import {AssetGraphLiveQuery_assetNodes_freshnessPolicy} from './types/AssetGraphLiveQuery';
import {AssetNodeFragment} from './types/AssetNodeFragment';

const MISSING_LIVE_DATA: LiveDataForNode = {
  unstartedRunIds: [],
  inProgressRunIds: [],
  runWhichFailedToMaterialize: null,
  freshnessInfo: null,
  freshnessPolicy: null,
  lastMaterialization: null,
  lastMaterializationRunStatus: null,
  lastObservation: null,
  currentLogicalVersion: null,
  projectedLogicalVersion: null,
  computeStatus: AssetComputeStatus.NONE,
  stepKey: '',
};

const VERSION_COLORS = {
  sourceBackground: Colors.Gray50,
  sourceText: undefined,
  staleBackground: Colors.Yellow50,
  okBackground: Colors.Green200,
  staleText: Colors.Yellow700,
  okText: undefined,
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

  const displayName = definition.assetKey.path[definition.assetKey.path.length - 1];

  const {
    lastMaterialization,
    lastObservation,
    currentLogicalVersion,
    projectedLogicalVersion,
    computeStatus,
  } = liveData || MISSING_LIVE_DATA;

  let staleStatus: 'ok' | 'never' | 'out-of-sync';
  if (definition.isSource) {
    staleStatus = 'ok';
  } else if (computeStatus === AssetComputeStatus.NONE) {
    staleStatus = 'never';
  } else {
    staleStatus = currentLogicalVersion === projectedLogicalVersion ? 'ok' : 'out-of-sync';
  }
  const isStale = staleStatus === 'never' || staleStatus === 'out-of-sync';

  return (
    <AssetInsetForHoverEffect>
      <AssetNodeContainer $selected={selected}>
        <AssetNodeBox $selected={selected}>
          <Name $isSource={definition.isSource}>
            <span style={{marginTop: 1}}>
              <Icon name={definition.isSource ? 'source_asset' : 'asset'} />
            </span>
            <div style={{overflow: 'hidden', textOverflow: 'ellipsis', marginTop: -1}}>
              {withMiddleTruncation(displayName, {
                maxLength: ASSET_NODE_NAME_MAX_LENGTH,
              })}
            </div>
            <div style={{flex: 1}} />
            <div style={{maxWidth: ASSET_NODE_ANNOTATIONS_MAX_WIDTH}}>
              <StaleNotice staleStatus={staleStatus} />
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

          {definition.isSource && !definition.isObservable ? null : (
            <Stats>
              {definition.isSource ? (
                lastObservation ? (
                  <StatsRow>
                    <span>Observed</span>
                    <CaptionMono style={{textAlign: 'right'}}>
                      <AssetRunLink
                        runId={lastObservation.runId}
                        event={{stepKey, timestamp: lastObservation.timestamp}}
                      >
                        <TimestampDisplay
                          timestamp={Number(lastObservation.timestamp) / 1000}
                          timeFormat={{showSeconds: false, showTimezone: false}}
                        />
                      </AssetRunLink>
                    </CaptionMono>
                  </StatsRow>
                ) : (
                  <>
                    <StatsRow>
                      <span>Observed</span>
                      <span>–</span>
                    </StatsRow>
                  </>
                )
              ) : lastMaterialization ? (
                <StatsRow>
                  <span>Materialized</span>
                  <CaptionMono style={{textAlign: 'right'}}>
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
              )
            )}
            {!definition.isSource && (
              <>
                <StatsRow>
                  <span>Latest&nbsp;Run</span>
                  <CaptionMono style={{textAlign: 'right'}}>
                    <AssetLatestRunWithNotices liveData={liveData} />
                  </CaptionMono>
                </StatsRow>
                {definition.opVersion && definition.opVersion !== 'DEFAULT' && (
              )}
              {!definition.isSource && (
                <>
                  <StatsRow>
                    <span>Latest&nbsp;Run</span>
                    <CaptionMono style={{textAlign: 'right'}}>
                      <AssetLatestRunWithNotices liveData={liveData} />
                    </CaptionMono>
                  </StatsRow>
                  {definition.opVersion && definition.opVersion !== 'DEFAULT' && (
                    <StatsRow>
                      <span>Code Version</span>
                      <CaptionMono style={{textAlign: 'right'}}>{definition.opVersion}</CaptionMono>
                    </StatsRow>
                  )}
                </>
              )}
              {currentLogicalVersion && (definition.isSource || lastMaterialization) && (
                <StatsRow>
                  <span style={{color: isStale ? VERSION_COLORS.staleText : VERSION_COLORS.okText}}>
                    Logical Version
                  </span>
                  <CaptionMono style={{textAlign: 'right'}}>
                    <LogicalVersion
                      isSource={definition.isSource}
                      isStale={isStale}
                      value={currentLogicalVersion}
                    />
                  </CaptionMono>
                </StatsRow>
              )}
              {isStale && lastMaterialization && projectedLogicalVersion && (
                <StatsRow>
                  <span style={{color: VERSION_COLORS.staleText}}>Projected Logical Version</span>
                  <CaptionMono style={{textAlign: 'right'}}>
                    <LogicalVersion
                      isSource={definition.isSource}
                      isStale={isStale}
                      value={projectedLogicalVersion}
                    />
                  </CaptionMono>
                </StatsRow>
              )}
            </Stats>
          )}
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
    </AssetInsetForHoverEffect>
  );
}, isEqual);

export const AssetNodeMinimal: React.FC<{
  selected: boolean;
  definition: AssetNodeFragment;
}> = ({selected, definition}) => {
  const displayName = definition.assetKey.path[definition.assetKey.path.length - 1];

  return (
    <AssetInsetForHoverEffect>
      <MinimalAssetNodeContainer $selected={selected}>
        <MinimalAssetNodeBox $selected={selected}>
          <MinimalName style={{fontSize: 28}} $isSource={definition.isSource}>
            {withMiddleTruncation(displayName, {maxLength: 17})}
          </MinimalName>
        </MinimalAssetNodeBox>
      </MinimalAssetNodeContainer>
    </AssetInsetForHoverEffect>
  );
};

export const AssetRunLink: React.FC<{
  runId: string;
  event?: Parameters<typeof linkToRunEvent>[1];
}> = ({runId, children, event}) => (
  <CaptionMono>
    <Link
      to={event ? linkToRunEvent({runId}, event) : `/instance/runs/${runId}`}
      target="_blank"
      rel="noreferrer"
    >
      {children || titleForRun({runId})}
    </Link>
  </CaptionMono>
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
    freshnessPolicy {
      maximumLagMinutes
      cronSchedule
    }
    freshnessInfo {
      currentMinutesLate
    }
    assetObservations(limit: 1) {
      timestamp
      runId
    }
    currentLogicalVersion
    projectedLogicalVersion
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
    opVersion
    description
    computeKind
    isSource
    assetKey {
      path
    }
    isObservable
  }
`;

const BoxColors = {
  Divider: 'rgba(219, 219, 244, 1)',
  Description: 'rgba(245, 245, 250, 1)',
  Stats: 'rgba(236, 236, 248, 1)',
};

const AssetInsetForHoverEffect = styled.div`
  padding: 10px 4px 2px 4px;
  height: 100%;
`;

export const AssetNodeContainer = styled.div<{$selected: boolean}>`
  outline: ${(p) => (p.$selected ? `2px dashed ${NodeHighlightColors.Border}` : 'none')};
  border-radius: 6px;
  outline-offset: -1px;
  background: ${(p) => (p.$selected ? NodeHighlightColors.Background : 'white')};
  padding: 4px;
`;

export const AssetNodeBox = styled.div<{$selected: boolean}>`
  border: 2px solid ${(p) => (p.$selected ? Colors.Blue500 : Colors.Blue200)};
  background: ${BoxColors.Stats};
  border-radius: 5px;
  position: relative;
  &:hover {
    box-shadow: ${Colors.Blue200} inset 0px 0px 0px 1px, rgba(0, 0, 0, 0.12) 0px 2px 12px 0px;
  }
`;

const Name = styled.div<{$isSource: boolean}>`
  /** Keep in sync with DISPLAY_NAME_PX_PER_CHAR */
  display: flex;
  padding: 4px 6px;
  background: ${(p) => (p.$isSource ? Colors.Gray200 : Colors.White)};
  font-family: ${FontFamily.monospace};
  border-top-left-radius: 5px;
  border-top-right-radius: 5px;
  font-weight: 600;
  gap: 4px;
`;

const MinimalAssetNodeContainer = styled(AssetNodeContainer)`
  border-radius: 12px;
  outline-offset: 2px;
  outline-width: 4px;
  height: 100%;
`;

const MinimalAssetNodeBox = styled(AssetNodeBox)`
  background: ${Colors.White};
  border: 4px solid ${Colors.Blue200};
  border-radius: 10px;
  position: relative;
  padding: 4px;
  height: 100%;
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

export const VersionedBadge = styled.div<{$isStale: boolean; $isSource: boolean}>`
  /** Keep in sync with DISPLAY_NAME_PX_PER_CHAR */
  padding: 2px 5px;
  background: ${(p) =>
    p.$isSource
      ? VERSION_COLORS.sourceBackground
      : p.$isStale
      ? VERSION_COLORS.staleBackground
      : VERSION_COLORS.okBackground};
  color: ${(p) => (p.$isStale ? VERSION_COLORS.staleText : VERSION_COLORS.okText)};
  font-family: ${FontFamily.monospace};
  border-radius: 5px;
  font-weight: 600;
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

const STALE_OVERDUE_MSG = `A materialization incorporating more recent upstream data is overdue.`;
const STALE_UNMATERIALIZED_MSG = `This asset has never been materialized.`;

const LogicalVersionTag = styled.div<{$isSource: boolean; $isStale: boolean}>`
  background: ${(p) =>
    p.$isSource
      ? VERSION_COLORS.sourceBackground
      : p.$isStale
      ? VERSION_COLORS.staleBackground
      : VERSION_COLORS.okBackground};
  color: ${(p) => (p.$isStale ? VERSION_COLORS.staleText : VERSION_COLORS.okText)};
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80px;
  padding: 0 4px;
`;

const LogicalVersion: React.FC<{
  value: string;
  isStale: boolean;
  isSource: boolean;
}> = ({value, isStale, isSource}) => (
  <Box flex={{gap: 4, alignItems: 'center'}}>
    <Tooltip content={value}>
      <LogicalVersionTag $isSource={isSource} $isStale={isStale}>
        {value}
      </LogicalVersionTag>
    </Tooltip>
  </Box>
);

const StaleNotice: React.FC<{staleStatus: 'ok' | 'never' | 'out-of-sync'}> = ({staleStatus}) => {
  if (staleStatus === 'ok') {
    return null;
  } else if (staleStatus === 'never') {
    return (
      <UpstreamNotice>
        never
        <br />
        materialized
      </UpstreamNotice>
    );
  } else {
    return (
      <UpstreamNotice>
        upstream
        <br />
        changed
      </UpstreamNotice>
    );
  }
};

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
  includeFreshness?: boolean;
}> = ({liveData, includeFreshness}) => {
  const {
    lastMaterialization,
    lastMaterializationRunStatus,
    unstartedRunIds,
    inProgressRunIds,
    runWhichFailedToMaterialize,
    stepKey,
  } = liveData || MISSING_LIVE_DATA;

  const buildRunTagContent = () => {
    if (inProgressRunIds?.length > 0) {
      return (
        <Box flex={{gap: 4, alignItems: 'center'}}>
          <Tooltip content="A run is currently rematerializing this asset.">
            <Spinner purpose="caption-text" />
          </Tooltip>
          <AssetRunLink runId={inProgressRunIds[0]} />
        </Box>
      );
    }
    if (unstartedRunIds?.length > 0) {
      return (
        <Box flex={{gap: 4, alignItems: 'center'}}>
          <Tooltip content="A run has started that will rematerialize this asset soon.">
            <Spinner purpose="caption-text" stopped />
          </Tooltip>
          <AssetRunLink runId={unstartedRunIds[0]} />
        </Box>
      );
    }
    if (runWhichFailedToMaterialize?.__typename === 'Run') {
      return (
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
      );
    }
    if (lastMaterialization) {
      return (
        <Box flex={{gap: 6, alignItems: 'center'}}>
          {lastMaterializationRunStatus ? (
            <RunStatusIndicator status={lastMaterializationRunStatus} size={10} />
          ) : (
            <div style={{width: 10}} />
          )}
          <AssetRunLink
            runId={lastMaterialization.runId}
            event={{stepKey, timestamp: lastMaterialization.timestamp}}
          />
        </Box>
      );
    }
    return undefined;
  };

  const runTagContent = buildRunTagContent();

  if (!includeFreshness) {
    return runTagContent || <span>–</span>;
  }

  return (
    <Box flex={{direction: 'row', gap: 4}}>
      {runTagContent ? <Tag>{runTagContent}</Tag> : <span>–</span>}
      {liveData && <CurrentMinutesLateTag liveData={liveData} policyOnHover />}
    </Box>
  );
};

export const CurrentMinutesLateTag: React.FC<{
  liveData: LiveDataForNode;
  policyOnHover?: boolean;
}> = ({liveData, policyOnHover}) => {
  const {freshnessInfo, freshnessPolicy} = liveData;
  const description = policyOnHover ? freshnessPolicyDescription(freshnessPolicy) : '';

  if (!freshnessInfo) {
    return <span />;
  }

  if (freshnessInfo.currentMinutesLate === null) {
    return (
      <Tooltip
        content={<div style={{maxWidth: 400}}>{`${STALE_UNMATERIALIZED_MSG} ${description}`}</div>}
      >
        <Tag intent="danger">Late</Tag>
      </Tooltip>
    );
  }

  if (freshnessInfo.currentMinutesLate === 0) {
    return description ? (
      <Tooltip content={freshnessPolicyDescription(freshnessPolicy)}>
        <Tag intent="success">Fresh</Tag>
      </Tooltip>
    ) : (
      <Tag intent="success">Fresh</Tag>
    );
  }

  return (
    <Tooltip content={<div style={{maxWidth: 400}}>{`${STALE_OVERDUE_MSG} ${description}`}</div>}>
      <Tag intent="danger">
        {moment
          .duration(freshnessInfo.currentMinutesLate, 'minute')
          .humanize(false, {m: 120, h: 48})}
        {' late'}
      </Tag>
    </Tooltip>
  );
};

export const freshnessPolicyDescription = (
  freshnessPolicy: AssetGraphLiveQuery_assetNodes_freshnessPolicy | null,
) => {
  if (!freshnessPolicy) {
    return '';
  }

  const {cronSchedule, maximumLagMinutes} = freshnessPolicy;

  const cronDesc = cronSchedule ? humanCronString(cronSchedule, 'UTC').replace(/^At /, '') : '';
  const lagDesc =
    maximumLagMinutes % 30 === 0
      ? `${maximumLagMinutes / 60} hour${maximumLagMinutes / 60 !== 1 ? 's' : ''}`
      : `${maximumLagMinutes} min`;

  if (cronDesc) {
    return `By ${cronDesc}, this asset should incorporate all data up to ${lagDesc} before that time.`;
  } else {
    return `At any point in time, this asset should incorporate all data up to ${lagDesc} before that time.`;
  }
};
