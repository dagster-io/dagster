import {gql} from '@apollo/client';
import {Colors, Icon, FontFamily, Box, Spinner, Tooltip, Body} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

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
import {LiveDataForNode} from './Utils';
import {ASSET_NODE_NAME_MAX_LENGTH} from './layout';
import {
  AssetNodeFragment,
  AssetNodeLiveMaterializationFragment,
  AssetNodeLiveObservationFragment,
} from './types/AssetNode.types';
import {AssetLatestInfoRunFragment} from './types/useLiveDataForAssetKeys.types';

export const AssetNode: React.FC<{
  definition: AssetNodeFragment;
  liveData?: LiveDataForNode;
  selected: boolean;
}> = React.memo(({definition, selected, liveData}) => {
  const displayName = definition.assetKey.path[definition.assetKey.path.length - 1];
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
            <div style={{overflow: 'hidden', textOverflow: 'ellipsis'}}>
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

function getStepKey(definition: {opNames: string[]}) {
  // Used for linking to the run with this step highlighted. We only support highlighting
  // a single step, so just use the first one.
  const firstOp = definition.opNames.length ? definition.opNames[0] : null;
  return firstOp || '';
}

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

type GenericStatusProps = {
  materializingRunId: string;
  lastObservation: AssetNodeLiveObservationFragment;
  liveData: LiveDataForNode;
  lastMaterialization: AssetNodeLiveMaterializationFragment;
  runWhichFailedToMaterialize: AssetLatestInfoRunFragment;
  currentMinutesLate: number;
  numPartitions: number;
  numFailed: number;
  numMissing: number;
  numMaterialized: number;
  numMaterializing: number;
  late: boolean;
};
export type StatusCaseObject =
  | {
      case: StatusCase.LOADING;
    }
  | ({
      case: StatusCase.SOURCE_OBSERVING;
    } & Pick<GenericStatusProps, 'materializingRunId' | 'liveData'>)
  | ({
      case: StatusCase.SOURCE_OBSERVED;
    } & Pick<GenericStatusProps, 'lastObservation' | 'liveData'>)
  | ({
      case: StatusCase.SOURCE_NEVER_OBSERVED;
    } & Pick<GenericStatusProps, 'liveData'>)
  | ({
      case: StatusCase.SOURCE_NO_STATE;
    } & Pick<GenericStatusProps, 'liveData'>)
  | ({
      case: StatusCase.MATERIALIZING;
    } & Pick<GenericStatusProps, 'liveData' | 'materializingRunId' | 'numMaterializing'>)
  | ({
      case: StatusCase.LATE_OR_FAILED;
      liveData: LiveDataForNode;
    } & Pick<GenericStatusProps, 'liveData' | 'currentMinutesLate' | 'late'> &
      Partial<Pick<GenericStatusProps, 'runWhichFailedToMaterialize'>>)
  | ({
      case: StatusCase.NEVER_MATERIALIZED;
    } & Pick<GenericStatusProps, 'liveData'>)
  | ({
      case: StatusCase.MATERIALIZED;
    } & Pick<GenericStatusProps, 'liveData'>)
  | ({
      case: StatusCase.PARTITIONS_FAILED;
    } & Pick<
      GenericStatusProps,
      | 'currentMinutesLate'
      | 'numFailed'
      | 'numMissing'
      | 'numPartitions'
      | 'liveData'
      | 'late'
      | 'numMaterialized'
    >)
  | ({
      case: StatusCase.PARTITIONS_MISSING;
    } & Pick<
      GenericStatusProps,
      | 'currentMinutesLate'
      | 'numFailed'
      | 'numMissing'
      | 'numPartitions'
      | 'liveData'
      | 'late'
      | 'numMaterialized'
    >)
  | ({
      case: StatusCase.PARTITIONS_MATERIALIZED;
    } & Pick<
      GenericStatusProps,
      | 'currentMinutesLate'
      | 'numFailed'
      | 'numMissing'
      | 'numPartitions'
      | 'liveData'
      | 'late'
      | 'numMaterialized'
    >);

/**
 *
 * This logic is based off `buildAssetNodeStatusContent`
 */
export function getAssetNodeStatusCase({
  definition,
  liveData,
}: {
  definition: {opNames: string[]; isSource: boolean; isObservable: boolean};
  liveData: LiveDataForNode | null | undefined;
}): StatusCaseObject {
  if (!liveData) {
    return {case: StatusCase.LOADING};
  }

  const {
    lastMaterialization,
    runWhichFailedToMaterialize,
    inProgressRunIds,
    unstartedRunIds,
  } = liveData;

  const materializingRunId = inProgressRunIds[0] || unstartedRunIds[0];
  const late = isAssetLate(liveData);
  const currentMinutesLate = liveData.freshnessInfo?.currentMinutesLate || 0;

  if (definition.isSource) {
    if (materializingRunId) {
      return {case: StatusCase.SOURCE_OBSERVING, materializingRunId, liveData};
    }
    if (liveData?.lastObservation) {
      return {
        case: StatusCase.SOURCE_OBSERVED,
        liveData,
        lastObservation: liveData.lastObservation,
      };
    }
    if (definition.isObservable) {
      return {case: StatusCase.SOURCE_NEVER_OBSERVED, liveData};
    }
    return {case: StatusCase.SOURCE_NO_STATE, liveData};
  }

  if (materializingRunId) {
    const numMaterializing = liveData.partitionStats?.numMaterializing || 0;
    return {case: StatusCase.MATERIALIZING, materializingRunId, liveData, numMaterializing};
  }

  if (liveData.partitionStats) {
    const {numPartitions, numMaterialized, numFailed} = liveData.partitionStats;
    const numMissing = numPartitions - numFailed - numMaterialized;

    return late || numFailed
      ? {
          case: StatusCase.PARTITIONS_FAILED,
          numPartitions,
          numMissing,
          numMaterialized,
          numFailed,
          liveData,
          late,
          currentMinutesLate,
        }
      : numMissing
      ? {
          case: StatusCase.PARTITIONS_MISSING,
          numPartitions,
          numMissing,
          numMaterialized,
          numFailed,
          liveData,
          late,
          currentMinutesLate,
        }
      : {
          case: StatusCase.PARTITIONS_MATERIALIZED,
          numPartitions,
          numMissing,
          numMaterialized,
          numFailed,
          liveData,
          late,
          currentMinutesLate,
        };
  }

  if (runWhichFailedToMaterialize || late) {
    return {
      case: StatusCase.LATE_OR_FAILED,
      liveData,
      late,
      runWhichFailedToMaterialize: runWhichFailedToMaterialize || undefined,
      currentMinutesLate,
    };
  }

  if (!lastMaterialization) {
    return {case: StatusCase.NEVER_MATERIALIZED, liveData};
  }

  return {case: StatusCase.MATERIALIZED, liveData};
}

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
  const statusCase = getAssetNodeStatusCase({definition, liveData});

  switch (statusCase.case) {
    case StatusCase.LOADING:
      return {
        background: Colors.Gray100,
        border: Colors.Gray300,
        content: (
          <>
            <Spinner purpose="caption-text" />
            <span style={{flex: 1, color: Colors.Gray800}}>Loading...</span>
          </>
        ),
      };
    case StatusCase.SOURCE_OBSERVING:
      return {
        background: Colors.Gray100,
        border: Colors.Gray300,
        content: (
          <>
            <AssetLatestRunSpinner liveData={statusCase.liveData} purpose="caption-text" />
            <span style={{flex: 1}} color={Colors.Gray800}>
              Observing...
            </span>
            {expanded && <SpacerDot />}
            <AssetRunLink runId={statusCase.materializingRunId} />
          </>
        ),
      };
    case StatusCase.SOURCE_OBSERVED:
      return {
        background: Colors.Gray100,
        border: Colors.Gray300,
        content: (
          <>
            {expanded && <AssetPartitionStatusDot status={[AssetPartitionStatus.MISSING]} />}
            <span>Observed</span>
            {expanded && <SpacerDot />}
            <span style={{textAlign: 'right', overflow: 'hidden'}}>
              <AssetRunLink
                runId={statusCase.lastObservation.runId}
                event={{
                  stepKey: getStepKey(definition),
                  timestamp: statusCase.lastObservation.timestamp,
                }}
              >
                <TimestampDisplay
                  timestamp={Number(statusCase.lastObservation.timestamp) / 1000}
                  timeFormat={{showSeconds: false, showTimezone: false}}
                />
              </AssetRunLink>
            </span>
          </>
        ),
      };
    case StatusCase.SOURCE_NEVER_OBSERVED:
      return {
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
    case StatusCase.SOURCE_NO_STATE:
      return {
        background: Colors.Gray100,
        border: Colors.Gray300,
        content: <span>–</span>,
      };
    case StatusCase.MATERIALIZING:
      return {
        background: Colors.Blue50,
        border: Colors.Blue500,
        content: (
          <>
            <div style={{marginLeft: -1, marginRight: -1}}>
              <AssetLatestRunSpinner liveData={statusCase.liveData} purpose="caption-text" />
            </div>
            <span style={{flex: 1}} color={Colors.Gray800}>
              {statusCase.numMaterializing === 1
                ? `Materializing 1 partition...`
                : statusCase.numMaterializing
                ? `Materializing ${statusCase.numMaterializing} partitions...`
                : `Materializing...`}
            </span>
            {expanded && <SpacerDot />}
            {!statusCase.numMaterializing || statusCase.numMaterializing === 1 ? (
              <AssetRunLink runId={statusCase.materializingRunId} />
            ) : undefined}
          </>
        ),
      };

    case StatusCase.PARTITIONS_FAILED:
    case StatusCase.PARTITIONS_MATERIALIZED:
    case StatusCase.PARTITIONS_MISSING:
      const {numPartitions, numMaterialized, numFailed, late} = statusCase;
      const numMissing = numPartitions - numFailed - numMaterialized;
      const {background, foreground, border} = StyleForAssetPartitionStatus[
        late || numFailed
          ? AssetPartitionStatus.FAILED
          : numMissing
          ? AssetPartitionStatus.MISSING
          : AssetPartitionStatus.MATERIALIZED
      ];
      return {
        background,
        border,
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
                content={humanizedLateString(
                  statusCase.liveData.freshnessInfo?.currentMinutesLate || 0,
                )}
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

  const lastMaterialization = statusCase.liveData.lastMaterialization;

  const lastMaterializationLink = lastMaterialization ? (
    <span style={{overflow: 'hidden'}}>
      <AssetRunLink
        runId={lastMaterialization.runId}
        event={{stepKey: getStepKey(definition), timestamp: lastMaterialization.timestamp}}
      >
        <TimestampDisplay
          timestamp={Number(lastMaterialization.timestamp) / 1000}
          timeFormat={{showSeconds: false, showTimezone: false}}
        />
      </AssetRunLink>
    </span>
  ) : undefined;

  switch (statusCase.case) {
    case StatusCase.LATE_OR_FAILED:
      return {
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

            {statusCase.late && statusCase.runWhichFailedToMaterialize ? (
              <Tooltip position="top" content={humanizedLateString(statusCase.currentMinutesLate)}>
                <span style={{color: Colors.Red700}}>Failed, Overdue</span>
              </Tooltip>
            ) : statusCase.late ? (
              <Tooltip position="top" content={humanizedLateString(statusCase.currentMinutesLate)}>
                <span style={{color: Colors.Red700}}>Overdue</span>
              </Tooltip>
            ) : statusCase.runWhichFailedToMaterialize ? (
              <span style={{color: Colors.Red700}}>Failed</span>
            ) : undefined}

            {expanded && <SpacerDot />}

            {statusCase.runWhichFailedToMaterialize ? (
              <span style={{overflow: 'hidden'}}>
                <AssetRunLink runId={statusCase.runWhichFailedToMaterialize.id}>
                  <TimestampDisplay
                    timestamp={Number(statusCase.runWhichFailedToMaterialize.endTime)}
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

    case StatusCase.NEVER_MATERIALIZED:
      return {
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
}

export const AssetNodeMinimal: React.FC<{
  selected: boolean;
  liveData?: LiveDataForNode;
  definition: AssetNodeFragment;
}> = ({selected, definition, liveData}) => {
  const {isSource, assetKey} = definition;
  const {border, background} = buildAssetNodeStatusContent({assetKey, definition, liveData});
  const displayName = assetKey.path[assetKey.path.length - 1];
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
const Name = styled.div<{$isSource: boolean}>`
  /** Keep in sync with DISPLAY_NAME_PX_PER_CHAR */
  display: flex;
  padding: 3px 6px;
  background: ${(p) => (p.$isSource ? Colors.Gray100 : Colors.Blue50)};
  font-family: ${FontFamily.monospace};
  border-top-left-radius: 7px;
  border-top-right-radius: 7px;
  font-weight: 600;
  gap: 4px;
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
