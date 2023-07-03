import {gql} from '@apollo/client';
import {Body, Box, Colors, FontFamily, Icon, Spinner, Tooltip} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import React from 'react';
import {Link} from 'react-router-dom';
import styled, {CSSObject} from 'styled-components/macro';

import {withMiddleTruncation} from '../app/Util';
import {
  PartitionCountTags,
  StyleForAssetPartitionStatus,
  partitionCountString,
} from '../assets/AssetNodePartitionCounts';
import {AssetPartitionStatusDot} from '../assets/AssetPartitionList';
import {AssetPartitionStatus} from '../assets/AssetPartitionStatus';
import {humanizedLateString, isAssetLate} from '../assets/CurrentMinutesLateTag';
import {StaleReasonsTags} from '../assets/Stale';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetComputeKindTag} from '../graph/OpTags';
import {AssetKeyInput} from '../graphql/types';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {markdownToPlaintext} from '../ui/markdownToPlaintext';

import {AssetLatestRunSpinner, AssetRunLink} from './AssetRunLinking';
import {LiveDataForNode, stepKeyForAsset} from './Utils';
import {ASSET_NODE_NAME_MAX_LENGTH} from './layout';
import {AssetNodeFragment} from './types/AssetNode.types';

export enum StatusCase {
  LOADING = 'LOADING',
  SOURCE_OBSERVING = 'SOURCE_OBSERVING',
  SOURCE_OBSERVED = 'SOURCE_OBSERVED',
  SOURCE_NEVER_OBSERVED = 'SOURCE_NEVER_OBSERVED',
  SOURCE_NO_STATE = 'SOURCE_NO_STATE',
  MATERIALIZING = 'MATERIALIZING',
  LATE_OR_FAILED = 'LATE_OR_FAILED',
  NEVER_MATERIALIZED = 'NEVER_MATERIALIZED',
  MATERIALIZED = 'MATERIALIZED',
  PARTITIONS_FAILED = 'PARTITIONS_FAILED',
  PARTITIONS_MISSING = 'PARTITIONS_MISSING',
  PARTITIONS_MATERIALIZED = 'PARTITIONS_MATERIALIZED',
}

export const AssetNode: React.FC<{
  definition: AssetNodeFragment;
  liveData?: LiveDataForNode;
  selected: boolean;
}> = React.memo(({definition, selected, liveData}) => {
  const displayName = definition.assetKey.path[definition.assetKey.path.length - 1]!;
  const isSource = definition.isSource;

  return (
    <AssetInsetForHoverEffect>
      <AssetTopTags definition={definition} liveData={liveData} />
      <AssetNodeContainer $selected={selected}>
        <AssetNodeBox $selected={selected} $isSource={isSource}>
          <Name $isSource={isSource}>
            <span style={{marginTop: 1}}>
              <Icon name={isSource ? 'source_asset' : 'asset'} />
            </span>
            <div
              data-tooltip={displayName}
              data-tooltip-style={isSource ? NameTooltipStyleSource : NameTooltipStyle}
              style={{overflow: 'hidden', textOverflow: 'ellipsis'}}
            >
              {withMiddleTruncation(displayName, {
                maxLength: ASSET_NODE_NAME_MAX_LENGTH,
              })}
            </div>
            <div style={{flex: 1}} />
          </Name>
          <Box
            style={{padding: '6px 8px'}}
            flex={{direction: 'column', gap: 4}}
            border={{side: 'top', width: 1, color: Colors.KeylineGray}}
          >
            {definition.description ? (
              <Description $color={Colors.Gray800}>
                {markdownToPlaintext(definition.description).split('\n')[0]}
              </Description>
            ) : (
              <Description $color={Colors.Gray400}>No description</Description>
            )}
            {definition.isPartitioned && (
              <PartitionCountTags definition={definition} liveData={liveData} />
            )}
            <StaleReasonsTags liveData={liveData} assetKey={definition.assetKey} include="self" />
          </Box>

          {isSource && !definition.isObservable ? null : (
            <AssetNodeStatusRow definition={definition} liveData={liveData} />
          )}
          <AssetComputeKindTag definition={definition} style={{right: -2, paddingTop: 7}} />
        </AssetNodeBox>
      </AssetNodeContainer>
    </AssetInsetForHoverEffect>
  );
}, isEqual);

const AssetTopTags: React.FC<{
  definition: AssetNodeFragment;
  liveData?: LiveDataForNode;
}> = ({definition, liveData}) => (
  <Box flex={{gap: 4}} padding={{left: 4}} style={{height: 24}}>
    <StaleReasonsTags liveData={liveData} assetKey={definition.assetKey} include="upstream" />
  </Box>
);

const AssetNodeStatusBox: React.FC<{background: string; children: React.ReactNode}> = ({
  background,
  children,
}) => (
  <Box
    padding={{horizontal: 8}}
    style={{
      borderBottomLeftRadius: 6,
      borderBottomRightRadius: 6,
      whiteSpace: 'nowrap',
      lineHeight: '12px',
      fontSize: 12,
      height: 24,
    }}
    flex={{justifyContent: 'space-between', alignItems: 'center', gap: 6}}
    background={background}
  >
    {children}
  </Box>
);

interface StatusRowProps {
  definition: AssetNodeFragment;
  liveData: LiveDataForNode | undefined;
}

const AssetNodeStatusRow: React.FC<StatusRowProps> = ({definition, liveData}) => {
  const {content, background} = buildAssetNodeStatusContent({
    assetKey: definition.assetKey,
    definition,
    liveData,
  });
  return <AssetNodeStatusBox background={background}>{content}</AssetNodeStatusBox>;
};

export function buildAssetNodeStatusContent({
  assetKey,
  definition,
  liveData,
  expanded,
}: {
  assetKey: AssetKeyInput;
  definition: {opNames: string[]; isSource: boolean; isObservable: boolean};
  liveData: LiveDataForNode | null | undefined;
  expanded?: boolean;
}) {
  if (!liveData) {
    return {
      case: StatusCase.LOADING,
      background: Colors.Gray100,
      border: Colors.Gray300,
      content: (
        <>
          <Spinner purpose="caption-text" />
          <span style={{flex: 1, color: Colors.Gray800}}>Loading...</span>
        </>
      ),
    };
  }

  const {
    lastMaterialization,
    runWhichFailedToMaterialize,
    inProgressRunIds,
    unstartedRunIds,
  } = liveData;

  const materializingRunId = inProgressRunIds[0] || unstartedRunIds[0];
  const late = isAssetLate(liveData);

  if (definition.isSource) {
    if (materializingRunId) {
      return {
        case: StatusCase.SOURCE_OBSERVING,
        background: Colors.Gray100,
        border: Colors.Gray300,
        content: (
          <>
            <AssetLatestRunSpinner liveData={liveData} purpose="caption-text" />
            <span style={{flex: 1}} color={Colors.Gray800}>
              Observing...
            </span>
            {expanded && <SpacerDot />}
            <AssetRunLink runId={materializingRunId} />
          </>
        ),
      };
    }
    if (liveData?.lastObservation) {
      return {
        case: StatusCase.SOURCE_OBSERVED,
        background: Colors.Gray100,
        border: Colors.Gray300,
        content: (
          <>
            {expanded && <AssetPartitionStatusDot status={[AssetPartitionStatus.MISSING]} />}
            <span>Observed</span>
            {expanded && <SpacerDot />}
            <span style={{textAlign: 'right', overflow: 'hidden'}}>
              <AssetRunLink
                runId={liveData.lastObservation.runId}
                event={{
                  stepKey: stepKeyForAsset(definition),
                  timestamp: liveData.lastObservation.timestamp,
                }}
              >
                <TimestampDisplay
                  timestamp={Number(liveData.lastObservation.timestamp) / 1000}
                  timeFormat={{showSeconds: false, showTimezone: false}}
                />
              </AssetRunLink>
            </span>
          </>
        ),
      };
    }
    if (definition.isObservable) {
      return {
        case: StatusCase.SOURCE_NEVER_OBSERVED,
        background: Colors.Gray100,
        border: Colors.Gray300,
        content: (
          <>
            {expanded && (
              <Icon
                name="partition_missing"
                color={Colors.Gray300}
                style={{marginRight: -2}}
                size={12}
              />
            )}
            <span>Never observed</span>
            {!expanded && <span>–</span>}
          </>
        ),
      };
    }

    return {
      case: StatusCase.SOURCE_NO_STATE,
      background: Colors.Gray100,
      border: Colors.Gray300,
      content: <span>–</span>,
    };
  }

  if (materializingRunId) {
    // Note: this value is undefined for unpartitioned assets
    const numMaterializing = liveData.partitionStats?.numMaterializing;

    return {
      case: StatusCase.MATERIALIZING,
      background: Colors.Blue50,
      border: Colors.Blue500,
      numMaterializing,
      content: (
        <>
          <div style={{marginLeft: -1, marginRight: -1}}>
            <AssetLatestRunSpinner liveData={liveData} purpose="caption-text" />
          </div>
          <span style={{flex: 1}} color={Colors.Gray800}>
            {numMaterializing === 1
              ? `Materializing 1 partition...`
              : numMaterializing
              ? `Materializing ${numMaterializing} partitions...`
              : `Materializing...`}
          </span>
          {expanded && <SpacerDot />}
          {!numMaterializing || numMaterializing === 1 ? (
            <AssetRunLink runId={materializingRunId} />
          ) : undefined}
        </>
      ),
    };
  }

  if (liveData.partitionStats) {
    const {numPartitions, numMaterialized, numFailed} = liveData.partitionStats;
    const numMissing = numPartitions - numFailed - numMaterialized;
    const {background, foreground, border} = StyleForAssetPartitionStatus[
      late || numFailed
        ? AssetPartitionStatus.FAILED
        : numMissing
        ? AssetPartitionStatus.MISSING
        : AssetPartitionStatus.MATERIALIZED
    ];
    const statusCase =
      late || numFailed
        ? StatusCase.PARTITIONS_FAILED
        : numMissing
        ? StatusCase.PARTITIONS_MISSING
        : StatusCase.PARTITIONS_MATERIALIZED;

    return {
      case: statusCase,
      background,
      border,
      numPartitions,
      numMissing,
      numFailed,
      numMaterialized,
      content: (
        <Link
          to={assetDetailsPathForKey(assetKey, {view: 'partitions'})}
          style={{color: foreground}}
          target="_blank"
          rel="noreferrer"
        >
          {late ? (
            <Tooltip
              position="top"
              content={humanizedLateString(liveData.freshnessInfo.currentMinutesLate)}
            >
              Overdue
            </Tooltip>
          ) : (
            partitionCountString(numPartitions)
          )}
        </Link>
      ),
    };
  }

  const lastMaterializationLink = lastMaterialization ? (
    <span style={{overflow: 'hidden'}}>
      <AssetRunLink
        runId={lastMaterialization.runId}
        event={{stepKey: stepKeyForAsset(definition), timestamp: lastMaterialization.timestamp}}
      >
        <TimestampDisplay
          timestamp={Number(lastMaterialization.timestamp) / 1000}
          timeFormat={{showSeconds: false, showTimezone: false}}
        />
      </AssetRunLink>
    </span>
  ) : undefined;

  if (runWhichFailedToMaterialize || late) {
    return {
      case: StatusCase.LATE_OR_FAILED,
      background: Colors.Red50,
      border: Colors.Red500,
      content: (
        <>
          {expanded && (
            <Icon
              name="partition_failure"
              color={Colors.Red500}
              style={{marginRight: -2}}
              size={12}
            />
          )}

          {late && runWhichFailedToMaterialize ? (
            <Tooltip
              position="top"
              content={humanizedLateString(liveData.freshnessInfo.currentMinutesLate)}
            >
              <span style={{color: Colors.Red700}}>Failed, Overdue</span>
            </Tooltip>
          ) : late ? (
            <Tooltip
              position="top"
              content={humanizedLateString(liveData.freshnessInfo.currentMinutesLate)}
            >
              <span style={{color: Colors.Red700}}>Overdue</span>
            </Tooltip>
          ) : runWhichFailedToMaterialize ? (
            <span style={{color: Colors.Red700}}>Failed</span>
          ) : undefined}

          {expanded && <SpacerDot />}

          {runWhichFailedToMaterialize ? (
            <span style={{overflow: 'hidden'}}>
              <AssetRunLink runId={runWhichFailedToMaterialize.id}>
                <TimestampDisplay
                  timestamp={Number(runWhichFailedToMaterialize.endTime)}
                  timeFormat={{showSeconds: false, showTimezone: false}}
                />
              </AssetRunLink>
            </span>
          ) : (
            lastMaterializationLink
          )}
        </>
      ),
    };
  }

  if (!lastMaterialization) {
    return {
      case: StatusCase.NEVER_MATERIALIZED,
      background: Colors.Yellow50,
      border: Colors.Yellow500,
      content: (
        <>
          {expanded && (
            <Icon
              name="partition_missing"
              color={Colors.Yellow500}
              style={{marginRight: -2}}
              size={12}
            />
          )}
          <span style={{color: Colors.Yellow700}}>Never materialized</span>
        </>
      ),
    };
  }

  return {
    case: StatusCase.MATERIALIZED,
    background: Colors.Green50,
    border: Colors.Green500,
    content: (
      <>
        {expanded && <AssetPartitionStatusDot status={[AssetPartitionStatus.MATERIALIZED]} />}
        <span style={{color: Colors.Green700}}>Materialized</span>
        {expanded && <SpacerDot />}
        {lastMaterializationLink}
      </>
    ),
  };
}

export const AssetNodeMinimal: React.FC<{
  selected: boolean;
  liveData?: LiveDataForNode;
  definition: AssetNodeFragment;
}> = ({selected, definition, liveData}) => {
  const {isSource, assetKey} = definition;
  const {border, background} = buildAssetNodeStatusContent({assetKey, definition, liveData});
  const displayName = assetKey.path[assetKey.path.length - 1]!;
  return (
    <AssetInsetForHoverEffect>
      <MinimalAssetNodeContainer $selected={selected}>
        <TooltipStyled
          content={displayName}
          canShow={displayName.length > 14}
          targetTagName="div"
          position="top"
        >
          <MinimalAssetNodeBox
            $selected={selected}
            $isSource={isSource}
            $background={background}
            $border={border}
          >
            <div
              style={{
                position: 'absolute',
                top: '50%',
                transform: 'translate(8px, -16px)',
              }}
            >
              <AssetLatestRunSpinner liveData={liveData} purpose="section" />
            </div>
            <MinimalName style={{fontSize: 30}} $isSource={isSource}>
              {withMiddleTruncation(displayName, {maxLength: 14})}
            </MinimalName>
          </MinimalAssetNodeBox>
        </TooltipStyled>
      </MinimalAssetNodeContainer>
    </AssetInsetForHoverEffect>
  );
};

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
      ...AssetNodeLiveMaterialization
    }
    assetObservations(limit: 1) {
      ...AssetNodeLiveObservation
    }
    freshnessInfo {
      ...AssetNodeLiveFreshnessInfo
    }
    staleStatus
    staleCauses {
      key {
        path
      }
      reason
      category
      dependency {
        path
      }
    }
    partitionStats {
      numMaterialized
      numMaterializing
      numPartitions
      numFailed
    }
  }

  fragment AssetNodeLiveFreshnessInfo on AssetFreshnessInfo {
    currentMinutesLate
  }

  fragment AssetNodeLiveMaterialization on MaterializationEvent {
    timestamp
    runId
  }

  fragment AssetNodeLiveObservation on ObservationEvent {
    timestamp
    runId
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
    hasMaterializePermission
    jobNames
    opNames
    opVersion
    description
    computeKind
    isPartitioned
    isObservable
    isSource
    assetKey {
      ...AssetNodeKey
    }
  }

  fragment AssetNodeKey on AssetKey {
    path
  }
`;

const AssetInsetForHoverEffect = styled.div`
  padding: 10px 4px 2px 4px;
  height: 100%;

  & *:focus {
    outline: 0;
  }
`;

const AssetNodeContainer = styled.div<{$selected: boolean}>`
  user-select: none;
  cursor: default;
  padding: 4px;
`;

const AssetNodeShowOnHover = styled.span`
  display: none;
`;

const AssetNodeBox = styled.div<{$isSource: boolean; $selected: boolean}>`
  ${(p) =>
    p.$isSource
      ? `border: 2px dashed ${p.$selected ? Colors.Gray600 : Colors.Gray300}`
      : `border: 2px solid ${p.$selected ? Colors.Blue500 : Colors.Blue200}`};

  ${(p) =>
    p.$isSource
      ? `outline: 3px solid ${p.$selected ? Colors.Gray300 : 'transparent'}`
      : `outline: 3px solid ${p.$selected ? Colors.Blue200 : 'transparent'}`};

  background: ${Colors.White};
  border-radius: 8px;
  position: relative;
  &:hover {
    box-shadow: rgba(0, 0, 0, 0.12) 0px 2px 12px 0px;
    ${AssetNodeShowOnHover} {
      display: initial;
    }
  }
`;

/** Keep in sync with DISPLAY_NAME_PX_PER_CHAR */
const NameCSS: CSSObject = {
  padding: '3px 6px',
  color: Colors.Gray800,
  fontFamily: FontFamily.monospace,
  fontWeight: 600,
};

const NameTooltipCSS: CSSObject = {
  ...NameCSS,
  top: -9,
  left: -12,
  fontSize: 16.8,
};

const NameTooltipStyle = JSON.stringify({
  ...NameTooltipCSS,
  background: Colors.Blue50,
  border: `1px solid ${Colors.Blue100}`,
});

const NameTooltipStyleSource = JSON.stringify({
  ...NameTooltipCSS,
  background: Colors.Gray100,
  border: `1px solid ${Colors.Gray200}`,
});

const Name = styled.div<{$isSource: boolean}>`
  ${NameCSS};
  display: flex;
  gap: 4px;
  background: ${(p) => (p.$isSource ? Colors.Gray100 : Colors.Blue50)};
`;

const MinimalAssetNodeContainer = styled(AssetNodeContainer)`
  padding-top: 30px;
  padding-bottom: 42px;
  height: 100%;
`;

const MinimalAssetNodeBox = styled.div<{
  $isSource: boolean;
  $selected: boolean;
  $background: string;
  $border: string;
}>`
  background: ${(p) => p.$background};
  ${(p) =>
    p.$isSource
      ? `border: 4px dashed ${p.$selected ? Colors.Gray500 : p.$border}`
      : `border: 4px solid ${p.$selected ? Colors.Blue500 : p.$border}`};

  ${(p) =>
    p.$isSource
      ? `outline: 8px solid ${p.$selected ? Colors.Gray300 : 'transparent'}`
      : `outline: 8px solid ${p.$selected ? Colors.Blue200 : 'transparent'}`};

  border-radius: 10px;
  position: relative;
  padding: 4px;
  height: 100%;
  min-height: 46px;
  &:hover {
    box-shadow: rgba(0, 0, 0, 0.12) 0px 2px 12px 0px;
  }
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

const Description = styled.div<{$color: string}>`
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: ${(p) => p.$color};
  font-size: 12px;
`;

const TooltipStyled = styled(Tooltip)`
  height: 100%;
`;

const SpacerDot = () => (
  <Body color={Colors.KeylineGray} style={{marginLeft: -3, marginRight: -3}}>
    •
  </Body>
);
