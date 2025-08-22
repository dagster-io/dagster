// eslint-disable-next-line no-restricted-imports
import {Intent} from '@blueprintjs/core';
import {
  Body,
  Box,
  Colors,
  HoverButton,
  Icon,
  IconName,
  Popover,
  Skeleton,
  SubtitleLarge,
  Tag,
  ifPlural,
} from '@dagster-io/ui-components';
import React, {useCallback, useMemo} from 'react';
import {Link} from 'react-router-dom';
import {observeEnabled} from 'shared/app/observeEnabled.oss';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {assertUnreachable} from '../app/Util';
import {useTrackEvent} from '../app/analytics';
import {useAssetHealthData} from '../asset-data/AssetHealthDataProvider';
import {
  AssetHealthCheckDegradedMetaFragment,
  AssetHealthCheckUnknownMetaFragment,
  AssetHealthCheckWarningMetaFragment,
  AssetHealthFragment,
  AssetHealthFreshnessMetaFragment,
  AssetHealthMaterializationDegradedNotPartitionedMetaFragment,
  AssetHealthMaterializationDegradedPartitionedMetaFragment,
  AssetHealthMaterializationHealthyPartitionedMetaFragment,
} from '../asset-data/types/AssetHealthDataProvider.types';
import {StatusCase} from '../asset-graph/AssetNodeStatusContent';
import {StatusCaseDot} from '../asset-graph/sidebar/util';
import {AssetHealthStatus, AssetKeyInput} from '../graphql/types';
import {TimeFromNow} from '../ui/TimeFromNow';
import {numberFormatter} from '../ui/formatters';

export const AssetHealthSummary = React.memo(
  ({assetKey, iconOnly}: {assetKey: {path: string[]}; iconOnly?: boolean}) => {
    if (!observeEnabled()) {
      return null;
    }

    return <AssetHealthSummaryImpl assetKey={assetKey} iconOnly={iconOnly} />;
  },
);

const AssetHealthSummaryImpl = React.memo(
  ({assetKey, iconOnly}: {assetKey: {path: string[]}; iconOnly?: boolean}) => {
    const {liveData} = useAssetHealthData(assetKey);
    const health = liveData?.assetHealth;

    const {primaryIcon, iconColor, intent, statusText} = useMemo(() => {
      return statusToIconAndColor[health?.assetHealth ?? 'undefined'];
    }, [health]);

    function content() {
      if (iconOnly) {
        return (
          <HoverButton style={{padding: 8}}>
            <Icon name={primaryIcon} color={iconColor} />
          </HoverButton>
        );
      }
      return (
        <Tag intent={intent} icon={primaryIcon}>
          {statusText}
        </Tag>
      );
    }

    if (!liveData) {
      if (iconOnly) {
        return (
          <div style={{padding: 11}}>
            <StatusCaseDot statusCase={StatusCase.LOADING} />
          </div>
        );
      }
      return <Skeleton $width={iconOnly ? 16 : 60} $height={16} />;
    }

    return (
      <AssetHealthSummaryPopover assetKey={assetKey} health={health}>
        {content()}
      </AssetHealthSummaryPopover>
    );
  },
);

export const AssetHealthSummaryPopover = ({
  health,
  assetKey,
  children,
}: {
  health: AssetHealthFragment['assetHealth'] | undefined;
  assetKey: AssetKeyInput;
  children: React.ReactNode;
}) => {
  const {primaryIcon, iconColor, statusText} = useMemo(() => {
    return statusToIconAndColor[health?.assetHealth ?? 'undefined'];
  }, [health]);

  return (
    <Popover
      interactionKind="hover"
      content={
        <div onClick={(e) => e.stopPropagation()}>
          <Box padding={12} flex={{direction: 'row', alignItems: 'center', gap: 6}} border="bottom">
            <Icon name={primaryIcon} color={iconColor} />
            <SubtitleLarge>{statusText}</SubtitleLarge>
          </Box>
          <Criteria
            assetKey={assetKey}
            status={health?.materializationStatus}
            metadata={health?.materializationStatusMetadata}
            type="materialization"
          />
          <Criteria
            assetKey={assetKey}
            status={health?.freshnessStatus}
            metadata={health?.freshnessStatusMetadata}
            type="freshness"
          />
          <Criteria
            assetKey={assetKey}
            status={health?.assetChecksStatus}
            metadata={health?.assetChecksStatusMetadata}
            type="checks"
          />
        </div>
      }
    >
      <div>{children}</div>
    </Popover>
  );
};

const Criteria = React.memo(
  ({
    status,
    metadata,
    type,
    assetKey,
  }: {
    assetKey: {path: string[]};
    status: AssetHealthStatus | undefined;
    metadata?:
      | AssetHealthCheckDegradedMetaFragment
      | AssetHealthCheckWarningMetaFragment
      | AssetHealthCheckUnknownMetaFragment
      | AssetHealthMaterializationDegradedNotPartitionedMetaFragment
      | AssetHealthMaterializationDegradedPartitionedMetaFragment
      | AssetHealthMaterializationHealthyPartitionedMetaFragment
      | AssetHealthFreshnessMetaFragment
      | undefined
      | null;
    type: 'materialization' | 'freshness' | 'checks';
  }) => {
    const {criteriaIcon, iconColor, textColor} = statusToIconAndColor[status ?? 'undefined'];

    const trackEvent = useTrackEvent();
    const onClick = useCallback(
      (name: string) => () => {
        trackEvent('asset-health-summary-click', {name});
      },
      [trackEvent],
    );

    const derivedExplanation = useMemo(() => {
      switch (metadata?.__typename) {
        case 'AssetHealthCheckUnknownMeta':
          if (metadata.numNotExecutedChecks > 0) {
            return (
              <Body>
                <Link
                  to={assetDetailsPathForKey(assetKey, {view: 'checks'})}
                  onClick={onClick('checks-unknown')}
                >
                  {numberFormatter.format(metadata.numNotExecutedChecks)} /{' '}
                  {numberFormatter.format(metadata.totalNumChecks)} check
                  {ifPlural(metadata.totalNumChecks, '', 's')} not executed
                </Link>
              </Body>
            );
          }
          return 'No checks executed';
        case 'AssetHealthCheckDegradedMeta':
          if (metadata.numWarningChecks > 0 && metadata.numFailedChecks > 0) {
            return (
              <Body>
                <Link
                  to={assetDetailsPathForKey(assetKey, {view: 'checks'})}
                  onClick={onClick('checks-degraded-all')}
                >
                  {numberFormatter.format(metadata.numWarningChecks)}/
                  {numberFormatter.format(metadata.totalNumChecks)} check
                  {ifPlural(metadata.totalNumChecks, '', 's')} warning,{' '}
                  {numberFormatter.format(metadata.numFailedChecks)}/
                  {numberFormatter.format(metadata.totalNumChecks)} check
                  {ifPlural(metadata.totalNumChecks, '', 's')} failed
                </Link>
              </Body>
            );
          }
          if (metadata.numWarningChecks > 0) {
            return (
              <Body>
                <Link
                  to={assetDetailsPathForKey(assetKey, {view: 'checks'})}
                  onClick={onClick('checks-degraded-warning')}
                >
                  {numberFormatter.format(metadata.numWarningChecks)}/
                  {numberFormatter.format(metadata.totalNumChecks)} check
                  {ifPlural(metadata.totalNumChecks, '', 's')} warning
                </Link>
              </Body>
            );
          }
          return (
            <Body>
              <Link
                to={assetDetailsPathForKey(assetKey, {view: 'checks'})}
                onClick={onClick('checks-degraded-failed')}
              >
                {numberFormatter.format(metadata.numFailedChecks)}/
                {numberFormatter.format(metadata.totalNumChecks)} check
                {ifPlural(metadata.totalNumChecks, '', 's')} failed
              </Link>
            </Body>
          );
        case 'AssetHealthCheckWarningMeta':
          return (
            <Body>
              <Link
                to={assetDetailsPathForKey(assetKey, {view: 'checks'})}
                onClick={onClick('checks-warning')}
              >
                {numberFormatter.format(metadata.numWarningChecks)}/
                {numberFormatter.format(metadata.totalNumChecks)} check
                {ifPlural(metadata.totalNumChecks, '', 's')} warning
              </Link>
            </Body>
          );
        case 'AssetHealthMaterializationDegradedNotPartitionedMeta':
          return (
            <Body>
              <Link
                to={`/runs/${metadata.failedRunId}`}
                onClick={onClick('materialization-degraded-not-partitioned')}
              >
                Materialization failed in run {metadata.failedRunId.split('-').shift()}
              </Link>
            </Body>
          );
        case 'AssetHealthMaterializationDegradedPartitionedMeta':
          return (
            <Body>
              <Link
                to={assetDetailsPathForKey(assetKey, {view: 'partitions', status: 'FAILED'})}
                onClick={onClick('degraded-partitioned')}
              >
                Materialization failed in {numberFormatter.format(metadata.numFailedPartitions)} out
                of {numberFormatter.format(metadata.totalNumPartitions)} partition
                {ifPlural(metadata.totalNumPartitions, '', 's')}
              </Link>
            </Body>
          );
        case 'AssetHealthMaterializationHealthyPartitionedMeta':
          return (
            <Body>
              <Link
                to={assetDetailsPathForKey(assetKey, {view: 'partitions', status: 'MISSING'})}
                onClick={onClick('healthy-missing-partitioned')}
              >
                Materialization missing in {numberFormatter.format(metadata.numMissingPartitions)}{' '}
                out of {numberFormatter.format(metadata.totalNumPartitions)} partition
                {ifPlural(metadata.totalNumPartitions, '', 's')}
              </Link>
            </Body>
          );
        case 'AssetHealthFreshnessMeta':
          if (metadata.lastMaterializedTimestamp === null) {
            return <Body>No materializations</Body>;
          }

          return (
            <Body>
              Last successfully materialized{' '}
              <TimeFromNow unixTimestamp={Number(metadata.lastMaterializedTimestamp)} />
            </Body>
          );
        case undefined:
          return null;
        default:
          assertUnreachable(metadata);
      }
    }, [metadata, assetKey, onClick]);

    const {text, shouldDim} = useMemo(() => {
      switch (type) {
        case 'materialization':
          switch (status) {
            case AssetHealthStatus.DEGRADED:
              return {text: 'Execution failed', shouldDim: false};
            case AssetHealthStatus.HEALTHY:
              return {text: 'Successfully executed', shouldDim: false};
            case AssetHealthStatus.WARNING:
              return {text: 'Execution warning', shouldDim: false};
            case undefined:
            case AssetHealthStatus.NOT_APPLICABLE:
              return {text: 'No executions', shouldDim: true};
            case AssetHealthStatus.UNKNOWN:
              return {text: 'Execution status unknown', shouldDim: true};
            default:
              assertUnreachable(status);
          }
        case 'freshness':
          switch (status) {
            case AssetHealthStatus.HEALTHY:
              return {text: 'Freshness policy passing', shouldDim: false};
            case AssetHealthStatus.DEGRADED:
              return {text: 'Freshness policy failed', shouldDim: false};
            case AssetHealthStatus.WARNING:
              return {text: 'Freshness policy warning', shouldDim: false};
            case undefined:
            case AssetHealthStatus.NOT_APPLICABLE:
              return {text: 'No freshness policy defined', shouldDim: true};
            case AssetHealthStatus.UNKNOWN:
              return {text: 'Freshness policy not evaluated', shouldDim: false};
            default:
              assertUnreachable(status);
          }
        case 'checks':
          switch (status) {
            case AssetHealthStatus.HEALTHY:
              return {text: 'All checks passed', shouldDim: false};
            case AssetHealthStatus.DEGRADED:
              if (metadata && 'numFailedChecks' in metadata && 'totalNumChecks' in metadata) {
                if (metadata.numFailedChecks === metadata.totalNumChecks) {
                  return {text: 'All checks failed', shouldDim: false};
                }
                return {text: 'Some checks failed', shouldDim: false};
              }
              return {text: 'Checks failed', shouldDim: false};
            case AssetHealthStatus.WARNING:
              if (metadata && 'numWarningChecks' in metadata && 'totalNumChecks' in metadata) {
                if (metadata.numWarningChecks === metadata.totalNumChecks) {
                  return {text: 'All checks failed', shouldDim: false};
                }
              }
              return {text: 'Some checks failed', shouldDim: false};
            case undefined:
            case AssetHealthStatus.NOT_APPLICABLE:
              return {text: 'No checks defined', shouldDim: true};
            case AssetHealthStatus.UNKNOWN:
              return {text: 'No checks evaluated', shouldDim: false};
            default:
              assertUnreachable(status);
          }
      }
    }, [type, status, metadata]);

    return (
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '20px 1fr',
          columnGap: 6,
          rowGap: 2,
          padding: '4px 12px',
          alignItems: 'center',
          opacity: shouldDim ? 0.5 : 1,
        }}
      >
        <Icon name={criteriaIcon} color={iconColor} style={{paddingTop: 2}} />
        <Body color={textColor}>{text}</Body>
        <div />
        <Body color={Colors.textLight()}>{derivedExplanation}</Body>
      </div>
    );
  },
);

export type AssetHealthStatusString = 'Unknown' | 'Degraded' | 'Warning' | 'Healthy';

export const STATUS_INFO: Record<
  AssetHealthStatusString | 'Not Applicable',
  {
    primaryIcon: IconName; // Main trend/status icon (e.g., 'successful_trend', 'failure_trend')
    simpleIcon: IconName; // Simple status icon (e.g., 'check_circle', 'cancel')
    criteriaIcon: IconName; // Icon used in detailed criteria breakdown
    iconColor: string;
    textColor: string;
    borderColor: string;
    statusText: AssetHealthStatusString; // Primary status display text
    intent: Intent;
    backgroundColor: string;
    hoverBackgroundColor: string;
    groupHeaderText: string; // Text used in grouped/header views
    materializationText: string; // Specific text for materialization status context
  }
> = {
  'Not Applicable': {
    primaryIcon: 'status',
    simpleIcon: 'missing',
    iconColor: Colors.textLight(),
    textColor: Colors.textDefault(),
    statusText: 'Unknown',
    groupHeaderText: 'None set',
    materializationText: 'Not applicable',
    intent: 'none',
    criteriaIcon: 'missing',
    borderColor: Colors.accentGray(),
    backgroundColor: Colors.backgroundGray(),
    hoverBackgroundColor: Colors.backgroundGrayHover(),
  },
  Unknown: {
    primaryIcon: 'status',
    simpleIcon: 'missing',
    iconColor: Colors.textLight(),
    textColor: Colors.textDefault(),
    statusText: 'Unknown',
    groupHeaderText: 'Not evaluated',
    intent: 'none',
    materializationText: 'Never materialized',
    criteriaIcon: 'missing',
    borderColor: Colors.accentGray(),
    backgroundColor: Colors.backgroundGray(),
    hoverBackgroundColor: Colors.backgroundGrayHover(),
  },
  Degraded: {
    primaryIcon: 'failure_trend',
    simpleIcon: 'cancel',
    criteriaIcon: 'close',
    materializationText: 'Failed',
    iconColor: Colors.accentRed(),
    textColor: Colors.textRed(),
    statusText: 'Degraded',
    groupHeaderText: 'Failed',
    intent: 'danger',
    borderColor: Colors.accentRed(),
    backgroundColor: Colors.backgroundRed(),
    hoverBackgroundColor: Colors.backgroundRedHover(),
  },
  Warning: {
    primaryIcon: 'warning_trend',
    simpleIcon: 'warning_outline',
    materializationText: 'Not applicable',
    criteriaIcon: 'warning_outline',
    iconColor: Colors.accentYellow(),
    statusText: 'Warning',
    groupHeaderText: 'Warning',
    textColor: Colors.textYellow(),
    borderColor: Colors.accentYellow(),
    backgroundColor: Colors.backgroundYellow(),
    hoverBackgroundColor: Colors.backgroundYellowHover(),
    intent: 'warning',
  },
  Healthy: {
    primaryIcon: 'successful_trend',
    simpleIcon: 'check_circle',
    criteriaIcon: 'done',
    materializationText: 'Success',
    iconColor: Colors.accentGreen(),
    textColor: Colors.textDefault(),
    statusText: 'Healthy',
    groupHeaderText: 'Passing',
    intent: 'success',
    borderColor: Colors.accentGreen(),
    backgroundColor: Colors.backgroundGreen(),
    hoverBackgroundColor: Colors.backgroundGreenHover(),
  },
};

export const statusToIconAndColor: Record<
  AssetHealthStatus | 'undefined',
  (typeof STATUS_INFO)[keyof typeof STATUS_INFO]
> = {
  ['undefined']: STATUS_INFO.Unknown,
  [AssetHealthStatus.NOT_APPLICABLE]: STATUS_INFO['Not Applicable'],
  [AssetHealthStatus.UNKNOWN]: STATUS_INFO.Unknown,
  [AssetHealthStatus.DEGRADED]: STATUS_INFO.Degraded,
  [AssetHealthStatus.HEALTHY]: STATUS_INFO.Healthy,
  [AssetHealthStatus.WARNING]: STATUS_INFO.Warning,
};
