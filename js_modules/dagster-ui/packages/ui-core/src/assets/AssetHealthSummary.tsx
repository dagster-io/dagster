// eslint-disable-next-line no-restricted-imports
import {Intent} from '@blueprintjs/core';
import {
  Body,
  Box,
  Colors,
  Icon,
  IconName,
  Popover,
  Skeleton,
  SubtitleLarge,
  Tag,
  ifPlural,
} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';
import {Link} from 'react-router-dom';
import dayjs from 'dayjs';


import {asAssetKeyInput} from './asInput';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {assertUnreachable} from '../app/Util';
import {useAssetHealthData} from '../asset-data/AssetHealthDataProvider';
import {
  AssetHealthCheckDegradedMetaFragment,
  AssetHealthCheckUnknownMetaFragment,
  AssetHealthCheckWarningMetaFragment,
  AssetHealthMaterializationDegradedNotPartitionedMetaFragment,
  AssetHealthMaterializationDegradedPartitionedMetaFragment,
  AssetHealthMaterializationWarningPartitionedMetaFragment,
  AssetHealthFreshnessMetaFragment,
} from '../asset-data/types/AssetHealthDataProvider.types';
import {AssetHealthStatus} from '../graphql/types';
import {numberFormatter} from '../ui/formatters';

export const AssetHealthSummary = React.memo(
  ({assetKey, iconOnly}: {assetKey: {path: string[]}; iconOnly?: boolean}) => {
    const key = useMemo(() => asAssetKeyInput(assetKey), [assetKey]);

    const {liveData} = useAssetHealthData(key);

    const health = liveData?.assetHealth;
    const {iconName, iconColor, intent, text} = useMemo(() => {
      return statusToIconAndColor[health?.assetHealth ?? 'undefined'];
    }, [health]);

    const icon = <Icon name={iconName} color={iconColor} />;

    function content() {
      if (iconOnly) {
        return icon;
      }
      return (
        <Tag intent={intent} icon={iconName}>
          {text}
        </Tag>
      );
    }

    if (!liveData) {
      return <Skeleton $width={iconOnly ? 16 : 60} $height={16} />;
    }

    return (
      <Popover
        interactionKind="hover"
        content={
          <div onClick={(e) => e.stopPropagation()}>
            <Box
              padding={12}
              flex={{direction: 'row', alignItems: 'center', gap: 6}}
              border="bottom"
            >
              {icon} <SubtitleLarge>{text}</SubtitleLarge>
            </Box>
            <Criteria
              assetKey={key}
              text="Successfully materialized in last run"
              status={health?.materializationStatus}
              metadata={health?.materializationStatusMetadata}
              explanation={
                !health || health?.materializationStatus === AssetHealthStatus.UNKNOWN
                  ? 'No materializations'
                  : undefined
              }
            />
            <Criteria
              assetKey={key}
              text="Has no freshness violations"
              status={health?.freshnessStatus}
              metadata={health?.freshnessStatusMetadata}
              explanation={
                !health || health?.freshnessStatus === AssetHealthStatus.NOT_APPLICABLE
                  ? 'No freshness policy defined'
                  : undefined
              }
            />
            <Criteria
              assetKey={key}
              text="Has no check errors"
              status={health?.assetChecksStatus}
              metadata={health?.assetChecksStatusMetadata}
              explanation={
                !health || health?.assetChecksStatus === AssetHealthStatus.UNKNOWN
                  ? 'No checks executed'
                  : health?.assetChecksStatus === AssetHealthStatus.NOT_APPLICABLE
                    ? 'No checks defined'
                    : undefined
              }
            />
          </div>
        }
      >
        {content()}
      </Popover>
    );
  },
);

const Criteria = React.memo(
  ({
    status,
    text,
    metadata,
    explanation,
    assetKey,
  }: {
    assetKey: {path: string[]};
    status: AssetHealthStatus | undefined;
    text: string;
    metadata?:
      | AssetHealthCheckDegradedMetaFragment
      | AssetHealthCheckWarningMetaFragment
      | AssetHealthCheckUnknownMetaFragment
      | AssetHealthMaterializationDegradedNotPartitionedMetaFragment
      | AssetHealthMaterializationDegradedPartitionedMetaFragment
      | AssetHealthMaterializationWarningPartitionedMetaFragment
      | AssetHealthFreshnessMetaFragment
      | undefined
      | null;
    explanation?: string;
  }) => {
    const {subStatusIconName, iconColor, textColor} = statusToIconAndColor[status ?? 'undefined'];

    const derivedExplanation = useMemo(() => {
      switch (metadata?.__typename) {
        case 'AssetHealthCheckUnknownMeta':
          if (metadata.numNotExecutedChecks > 0) {
            return (
              <Body>
                {numberFormatter.format(metadata.numNotExecutedChecks)} /{' '}
                {numberFormatter.format(metadata.totalNumChecks)}{' '}
                <Link to={assetDetailsPathForKey(assetKey, {view: 'checks'})}>
                  check
                  {ifPlural(metadata.totalNumChecks, '', 's')}
                </Link>{' '}
                not executed
              </Body>
            );
          }
          return 'No checks executed';
        case 'AssetHealthCheckDegradedMeta':
          if (metadata.numWarningChecks > 0 && metadata.numFailedChecks > 0) {
            return (
              <Body>
                {numberFormatter.format(metadata.numWarningChecks)}/
                {numberFormatter.format(metadata.totalNumChecks)}{' '}
                <Link to={assetDetailsPathForKey(assetKey, {view: 'checks'})}>
                  check
                  {ifPlural(metadata.totalNumChecks, '', 's')}
                </Link>{' '}
                warning, {numberFormatter.format(metadata.numFailedChecks)}/
                {numberFormatter.format(metadata.totalNumChecks)}{' '}
                <Link to={assetDetailsPathForKey(assetKey, {view: 'checks'})}>
                  check
                  {ifPlural(metadata.totalNumChecks, '', 's')}
                </Link>{' '}
                failed
              </Body>
            );
          }
          if (metadata.numWarningChecks > 0) {
            return (
              <Body>
                {numberFormatter.format(metadata.numWarningChecks)}/
                {numberFormatter.format(metadata.totalNumChecks)}{' '}
                <Link to={assetDetailsPathForKey(assetKey, {view: 'checks'})}>
                  check
                  {ifPlural(metadata.totalNumChecks, '', 's')}
                </Link>{' '}
                warning
              </Body>
            );
          }
          return (
            <Body>
              {numberFormatter.format(metadata.numFailedChecks)}/
              {numberFormatter.format(metadata.totalNumChecks)}{' '}
              <Link to={assetDetailsPathForKey(assetKey, {view: 'checks'})}>
                check
                {ifPlural(metadata.totalNumChecks, '', 's')}
              </Link>{' '}
              failed
            </Body>
          );
        case 'AssetHealthCheckWarningMeta':
          return (
            <Body>
              {numberFormatter.format(metadata.numWarningChecks)}/
              {numberFormatter.format(metadata.totalNumChecks)}{' '}
              <Link to={assetDetailsPathForKey(assetKey, {view: 'checks'})}>
                check
                {ifPlural(metadata.totalNumChecks, '', 's')}
              </Link>{' '}
              warning
            </Body>
          );
        case 'AssetHealthMaterializationDegradedNotPartitionedMeta':
          return (
            <Body>
              Materialization failed in run{' '}
              <Link to={`/runs/${metadata.failedRunId}`}>
                {metadata.failedRunId.split('-').shift()}
              </Link>
            </Body>
          );
        case 'AssetHealthMaterializationDegradedPartitionedMeta':
          return (
            <Body>
              Materialization missing in {numberFormatter.format(metadata.numMissingPartitions)} out
              of {numberFormatter.format(metadata.totalNumPartitions)}{' '}
              <Link to={assetDetailsPathForKey(assetKey, {view: 'partitions'})}>
                partition
                {ifPlural(metadata.totalNumPartitions, '', 's')}
              </Link>
            </Body>
          );
        case 'AssetHealthMaterializationWarningPartitionedMeta':
          return (
            <Body>
              Materialization missing in {numberFormatter.format(metadata.numMissingPartitions)} out
              of {numberFormatter.format(metadata.totalNumPartitions)}{' '}
              <Link to={assetDetailsPathForKey(assetKey, {view: 'partitions'})}>
                partition
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
              Last materialized {dayjs(Number(metadata.lastMaterializedTimestamp)).fromNow()} ago
            </Body>
          );
        case undefined:
          return null;
        default:
          assertUnreachable(metadata);
      }
    }, [metadata, assetKey]);

    return (
      <Box
        padding={{horizontal: 12, vertical: 4}}
        flex={{direction: 'row', alignItems: 'flex-start', gap: 6}}
      >
        <Icon name={subStatusIconName} color={iconColor} style={{paddingTop: 2}} />
        <Box flex={{direction: 'column', gap: 2}}>
          <Body color={textColor}>{text}</Body>
          <Body color={Colors.textLight()}>{explanation ?? derivedExplanation}</Body>
        </Box>
      </Box>
    );
  },
);

export type AssetHealthStatusString = 'Unknown' | 'Degraded' | 'Warning' | 'Healthy';

export const STATUS_INFO: Record<
  AssetHealthStatusString,
  {
    iconName: IconName;
    subStatusIconName: IconName;
    iconColor: string;
    textColor: string;
    text: AssetHealthStatusString;
    intent: Intent;
    backgroundColor: string;
    hoverBackgroundColor: string;
  }
> = {
  Unknown: {
    iconName: 'status',
    iconColor: Colors.textLight(),
    textColor: Colors.textDefault(),
    text: 'Unknown',
    intent: 'none',
    subStatusIconName: 'missing',
    backgroundColor: Colors.backgroundGray(),
    hoverBackgroundColor: Colors.backgroundGrayHover(),
  },
  Degraded: {
    iconName: 'failure_trend',
    subStatusIconName: 'close',
    iconColor: Colors.accentRed(),
    textColor: Colors.textRed(),
    text: 'Degraded',
    intent: 'danger',
    backgroundColor: Colors.backgroundRed(),
    hoverBackgroundColor: Colors.backgroundRedHover(),
  },
  Warning: {
    iconName: 'warning_trend',
    subStatusIconName: 'close',
    iconColor: Colors.accentYellow(),
    text: 'Warning',
    textColor: Colors.textYellow(),
    backgroundColor: Colors.backgroundYellow(),
    hoverBackgroundColor: Colors.backgroundYellowHover(),
    intent: 'warning',
  },
  Healthy: {
    iconName: 'successful_trend',
    subStatusIconName: 'done',
    iconColor: Colors.accentGreen(),
    textColor: Colors.textDefault(),
    text: 'Healthy',
    intent: 'success',
    backgroundColor: Colors.backgroundGreen(),
    hoverBackgroundColor: Colors.backgroundGreenHover(),
  },
};

export const statusToIconAndColor: Record<
  AssetHealthStatus | 'undefined',
  (typeof STATUS_INFO)[keyof typeof STATUS_INFO]
> = {
  ['undefined']: STATUS_INFO.Unknown,
  [AssetHealthStatus.NOT_APPLICABLE]: STATUS_INFO.Unknown,
  [AssetHealthStatus.UNKNOWN]: STATUS_INFO.Unknown,
  [AssetHealthStatus.DEGRADED]: STATUS_INFO.Degraded,
  [AssetHealthStatus.HEALTHY]: STATUS_INFO.Healthy,
  [AssetHealthStatus.WARNING]: STATUS_INFO.Warning,
};
