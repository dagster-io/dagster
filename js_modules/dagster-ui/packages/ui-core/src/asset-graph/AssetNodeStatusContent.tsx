import {Body, Colors, Icon, Spinner} from '@dagster-io/ui-components';
import React from 'react';
import {Link} from 'react-router-dom';

import {
  StyleForAssetPartitionStatus,
  partitionCountString,
} from '../assets/AssetNodePartitionCounts';
import {AssetPartitionStatusDot} from '../assets/AssetPartitionList';
import {AssetPartitionStatus} from '../assets/AssetPartitionStatus';
import {OverdueLineagePopover, isAssetOverdue} from '../assets/OverdueTag';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {
  AssetCheckExecutionResolvedStatus,
  AssetCheckSeverity,
  AssetKeyInput,
} from '../graphql/types';
import {TimestampDisplay} from '../schedules/TimestampDisplay';

import {AssetLatestRunSpinner, AssetRunLink} from './AssetRunLinking';
import {LiveDataForNode, stepKeyForAsset} from './Utils';

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

export type AssetNodeStatusContent = ReturnType<typeof buildAssetNodeStatusContent>;

const LOADING_STATUS_CONTENT = {
  case: StatusCase.LOADING as const,
  background: Colors.Gray100,
  border: Colors.Gray300,
  content: (
    <>
      <Spinner purpose="caption-text" />
      <span style={{flex: 1, color: Colors.Gray800}}>Loading...</span>
    </>
  ),
};

type StatusContentArgs = {
  assetKey: AssetKeyInput;
  definition: {opNames: string[]; isSource: boolean; isObservable: boolean};
  liveData: LiveDataForNode | null | undefined;
  expanded?: boolean;
};

export function buildAssetNodeStatusContent({
  assetKey,
  definition,
  liveData,
  expanded,
}: StatusContentArgs) {
  return definition.isSource
    ? _buildSourceAssetNodeStatusContent({
        assetKey,
        definition,
        liveData,
        expanded,
      })
    : _buildAssetNodeStatusContent({
        assetKey,
        definition,
        liveData,
        expanded,
      });
}

export function _buildSourceAssetNodeStatusContent({
  definition,
  liveData,
  expanded,
}: StatusContentArgs) {
  if (!liveData) {
    return LOADING_STATUS_CONTENT;
  }

  const {inProgressRunIds, unstartedRunIds} = liveData;
  const materializingRunId = inProgressRunIds[0] || unstartedRunIds[0];

  if (materializingRunId) {
    return {
      case: StatusCase.SOURCE_OBSERVING as const,
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
      case: StatusCase.SOURCE_OBSERVED as const,
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
      case: StatusCase.SOURCE_NEVER_OBSERVED as const,
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
    case: StatusCase.SOURCE_NO_STATE as const,
    background: Colors.Gray100,
    border: Colors.Gray300,
    content: <span>–</span>,
  };
}

export function _buildAssetNodeStatusContent({
  assetKey,
  definition,
  liveData,
  expanded,
}: StatusContentArgs) {
  if (!liveData) {
    return LOADING_STATUS_CONTENT;
  }

  const {lastMaterialization, runWhichFailedToMaterialize, inProgressRunIds, unstartedRunIds} =
    liveData;

  const materializingRunId = inProgressRunIds[0] || unstartedRunIds[0];
  const overdue = isAssetOverdue(liveData);
  const checksFailed = liveData.assetChecks.some(
    (c) =>
      (c.executionForLatestMaterialization?.status === AssetCheckExecutionResolvedStatus.FAILED &&
        c.executionForLatestMaterialization?.evaluation?.severity === AssetCheckSeverity.ERROR) ||
      c.executionForLatestMaterialization?.status ===
        AssetCheckExecutionResolvedStatus.EXECUTION_FAILED,
  );

  if (materializingRunId) {
    // Note: this value is undefined for unpartitioned assets
    const numMaterializing = liveData.partitionStats?.numMaterializing;

    return {
      case: StatusCase.MATERIALIZING as const,
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
    const {background, foreground, border} =
      StyleForAssetPartitionStatus[
        overdue || numFailed || checksFailed
          ? AssetPartitionStatus.FAILED
          : numMissing
          ? AssetPartitionStatus.MISSING
          : AssetPartitionStatus.MATERIALIZED
      ];
    const statusCase =
      overdue || numFailed || checksFailed
        ? (StatusCase.PARTITIONS_FAILED as const)
        : numMissing
        ? (StatusCase.PARTITIONS_MISSING as const)
        : (StatusCase.PARTITIONS_MATERIALIZED as const);

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
          {overdue ? (
            <OverdueLineagePopover assetKey={assetKey} liveData={liveData}>
              Overdue
            </OverdueLineagePopover>
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

  if (runWhichFailedToMaterialize || overdue || checksFailed) {
    return {
      case: StatusCase.LATE_OR_FAILED as const,
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

          {overdue && runWhichFailedToMaterialize ? (
            <OverdueLineagePopover assetKey={assetKey} liveData={liveData}>
              <span style={{color: Colors.Red700}}>Failed, Overdue</span>
            </OverdueLineagePopover>
          ) : overdue ? (
            <OverdueLineagePopover assetKey={assetKey} liveData={liveData}>
              <span style={{color: Colors.Red700}}>Overdue</span>
            </OverdueLineagePopover>
          ) : runWhichFailedToMaterialize ? (
            <span style={{color: Colors.Red700}}>Failed</span>
          ) : lastMaterialization ? (
            <span style={{color: Colors.Red700}}>Materialized</span>
          ) : (
            <span style={{color: Colors.Red700}}>Never materialized</span>
          )}

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
      case: StatusCase.NEVER_MATERIALIZED as const,
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
    case: StatusCase.MATERIALIZED as const,
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

const SpacerDot = () => (
  <Body color={Colors.KeylineGray} style={{marginLeft: -3, marginRight: -3}}>
    •
  </Body>
);
