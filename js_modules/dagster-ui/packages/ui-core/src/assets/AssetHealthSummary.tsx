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
  UnstyledButton,
  ifPlural,
} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import React, {useMemo} from 'react';
import {Link} from 'react-router-dom';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {asAssetKeyInput} from './asInput';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {featureEnabled} from '../app/Flags';
import {assertUnreachable} from '../app/Util';
import {useAssetHealthData} from '../asset-data/AssetHealthDataProvider';
import {
  AssetHealthCheckDegradedMetaFragment,
  AssetHealthCheckUnknownMetaFragment,
  AssetHealthCheckWarningMetaFragment,
  AssetHealthFreshnessMetaFragment,
  AssetHealthMaterializationDegradedNotPartitionedMetaFragment,
  AssetHealthMaterializationDegradedPartitionedMetaFragment,
  AssetHealthMaterializationWarningPartitionedMetaFragment,
} from '../asset-data/types/AssetHealthDataProvider.types';
import {AssetHealthStatus} from '../graphql/types';
import {numberFormatter} from '../ui/formatters';

export const AssetHealthSummary = React.memo(
  ({assetKey, iconOnly}: {assetKey: {path: string[]}; iconOnly?: boolean}) => {
    if (!featureEnabled(FeatureFlag.flagUseNewObserveUIs)) {
      return null;
    }

    return <AssetHealthSummaryImpl assetKey={assetKey} iconOnly={iconOnly} />;
  },
);

const AssetHealthSummaryImpl = React.memo(
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
        return (
          <UnstyledButton style={{display: 'flex', alignItems: 'center', padding: 8}}>
            {icon}
          </UnstyledButton>
        );
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
              status={health?.materializationStatus}
              metadata={health?.materializationStatusMetadata}
              type="materialization"
            />
            <Criteria
              assetKey={key}
              status={health?.freshnessStatus}
              metadata={health?.freshnessStatusMetadata}
              type="freshness"
            />
            <Criteria
              assetKey={key}
              status={health?.assetChecksStatus}
              metadata={health?.assetChecksStatusMetadata}
              type="checks"
            />
          </div>
        }
      >
        <div>{content()}</div>
      </Popover>
    );
  },
);

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
      | AssetHealthMaterializationWarningPartitionedMetaFragment
      | AssetHealthFreshnessMetaFragment
      | undefined
      | null;
    type: 'materialization' | 'freshness' | 'checks';
  }) => {
    const {subStatusIconName, iconColor, textColor} = statusToIconAndColor[status ?? 'undefined'];

    const derivedExplanation = useMemo(() => {
      switch (metadata?.__typename) {
        case 'AssetHealthCheckUnknownMeta':
          if (metadata.numNotExecutedChecks > 0) {
            return (
              <Body>
                <Link to={assetDetailsPathForKey(assetKey, {view: 'checks'})}>
                  {numberFormatter.format(metadata.numNotExecutedChecks)} /{' '}
                  {numberFormatter.format(metadata.totalNumChecks)} check{' '}
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
                <Link to={assetDetailsPathForKey(assetKey, {view: 'checks'})}>
                  {numberFormatter.format(metadata.numWarningChecks)}/
                  {numberFormatter.format(metadata.totalNumChecks)} check
                  {ifPlural(metadata.totalNumChecks, '', 's')} warning,{' '}
                  {numberFormatter.format(metadata.numFailedChecks)}/
                  {numberFormatter.format(metadata.totalNumChecks)} check
                  {ifPlural(metadata.totalNumChecks, '', 's')}
                  failed
                </Link>
              </Body>
            );
          }
          if (metadata.numWarningChecks > 0) {
            return (
              <Body>
                <Link to={assetDetailsPathForKey(assetKey, {view: 'checks'})}>
                  {numberFormatter.format(metadata.numWarningChecks)}/
                  {numberFormatter.format(metadata.totalNumChecks)} check
                  {ifPlural(metadata.totalNumChecks, '', 's')} warning
                </Link>
              </Body>
            );
          }
          return (
            <Body>
              <Link to={assetDetailsPathForKey(assetKey, {view: 'checks'})}>
                {numberFormatter.format(metadata.numFailedChecks)}/
                {numberFormatter.format(metadata.totalNumChecks)} check
                {ifPlural(metadata.totalNumChecks, '', 's')} failed
              </Link>
            </Body>
          );
        case 'AssetHealthCheckWarningMeta':
          return (
            <Body>
              <Link to={assetDetailsPathForKey(assetKey, {view: 'checks'})}>
                {numberFormatter.format(metadata.numWarningChecks)}/
                {numberFormatter.format(metadata.totalNumChecks)} check
                {ifPlural(metadata.totalNumChecks, '', 's')} warning
              </Link>
            </Body>
          );
        case 'AssetHealthMaterializationDegradedNotPartitionedMeta':
          return (
            <Body>
              <Link to={`/runs/${metadata.failedRunId}`}>
                Materialization failed in run {metadata.failedRunId.split('-').shift()}
              </Link>
            </Body>
          );
        case 'AssetHealthMaterializationDegradedPartitionedMeta':
          return (
            <Body>
              <Link to={assetDetailsPathForKey(assetKey, {view: 'partitions'})}>
                Materialization missing in {numberFormatter.format(metadata.numMissingPartitions)}{' '}
                out of {numberFormatter.format(metadata.totalNumPartitions)} partition
                {ifPlural(metadata.totalNumPartitions, '', 's')}
              </Link>
            </Body>
          );
        case 'AssetHealthMaterializationWarningPartitionedMeta':
          return (
            <Body>
              <Link to={assetDetailsPathForKey(assetKey, {view: 'partitions'})}>
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
              Last materialized {dayjs(Number(metadata.lastMaterializedTimestamp * 1000)).fromNow()}{' '}
              ago
            </Body>
          );
        case undefined:
          return null;
        default:
          assertUnreachable(metadata);
      }
    }, [metadata, assetKey]);

    const text = useMemo(() => {
      switch (type) {
        case 'materialization':
          switch (status) {
            case AssetHealthStatus.DEGRADED:
              return 'Failed to materialize';
            case AssetHealthStatus.HEALTHY:
              return 'Successfully materialized';
            // Warning case should not be possible for materializations
            case AssetHealthStatus.WARNING:
            case AssetHealthStatus.NOT_APPLICABLE:
            case AssetHealthStatus.UNKNOWN:
            case undefined:
              return 'No materializations';
            default:
              assertUnreachable(status);
          }
        case 'freshness':
          switch (status) {
            case AssetHealthStatus.HEALTHY:
              return 'Freshness policy passing';
            case AssetHealthStatus.DEGRADED:
              return 'Freshness policy failed';
            case AssetHealthStatus.WARNING:
              return 'Freshness policy warning';
            case undefined:
            case AssetHealthStatus.NOT_APPLICABLE:
              return 'No freshness policy defined';
            case AssetHealthStatus.UNKNOWN:
              return 'Freshness policy not evaluated';
            default:
              assertUnreachable(status);
          }
        case 'checks':
          switch (status) {
            case AssetHealthStatus.HEALTHY:
              return 'All checks passed';
            case AssetHealthStatus.DEGRADED:
              if (metadata && 'numFailedChecks' in metadata && 'totalNumChecks' in metadata) {
                if (metadata.numFailedChecks === metadata.totalNumChecks) {
                  return 'All checks failed';
                }
                return 'Some checks failed';
              }
              return 'Checks failed';
            case AssetHealthStatus.WARNING:
              if (metadata && 'numWarningChecks' in metadata && 'totalNumChecks' in metadata) {
                if (metadata.numWarningChecks === metadata.totalNumChecks) {
                  return 'All checks failed';
                }
              }
              return 'Some checks failed';
            case AssetHealthStatus.NOT_APPLICABLE:
              return 'No checks defined';
            case AssetHealthStatus.UNKNOWN:
            case undefined:
              return 'No checks evaluated';
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
        }}
      >
        <Icon name={subStatusIconName} color={iconColor} style={{paddingTop: 2}} />
        <Body color={textColor}>{text}</Body>
        <div />
        <Body color={Colors.textLight()}>{derivedExplanation}</Body>
      </div>
    );
  },
);

export type AssetHealthStatusString =
  | 'Unknown'
  | 'Degraded'
  | 'Warning'
  | 'Healthy'
  | 'Not Applicable';

export const STATUS_INFO: Record<
  AssetHealthStatusString,
  {
    iconName: IconName;
    iconName2: IconName;
    subStatusIconName: IconName;
    iconColor: string;
    textColor: string;
    text: AssetHealthStatusString;
    intent: Intent;
    backgroundColor: string;
    hoverBackgroundColor: string;
    text2: string;
  }
> = {
  'Not Applicable': {
    iconName: 'status',
    iconName2: 'missing',
    iconColor: Colors.textLight(),
    textColor: Colors.textDefault(),
    text: 'Unknown',
    text2: 'None set',
    intent: 'none',
    subStatusIconName: 'missing',
    backgroundColor: Colors.backgroundGray(),
    hoverBackgroundColor: Colors.backgroundGrayHover(),
  },
  Unknown: {
    iconName: 'status',
    iconName2: 'missing',
    iconColor: Colors.textLight(),
    textColor: Colors.textDefault(),
    text: 'Unknown',
    text2: 'Not evaluated',
    intent: 'none',
    subStatusIconName: 'missing',
    backgroundColor: Colors.backgroundGray(),
    hoverBackgroundColor: Colors.backgroundGrayHover(),
  },
  Degraded: {
    iconName: 'failure_trend',
    iconName2: 'cancel',
    subStatusIconName: 'close',
    iconColor: Colors.accentRed(),
    textColor: Colors.textRed(),
    text: 'Degraded',
    intent: 'danger',
    text2: 'Failed',
    backgroundColor: Colors.backgroundRed(),
    hoverBackgroundColor: Colors.backgroundRedHover(),
  },
  Warning: {
    iconName: 'warning_trend',
    iconName2: 'warning_outline',
    subStatusIconName: 'warning',
    iconColor: Colors.accentYellow(),
    text: 'Warning',
    text2: 'Warning',
    textColor: Colors.textYellow(),
    backgroundColor: Colors.backgroundYellow(),
    hoverBackgroundColor: Colors.backgroundYellowHover(),
    intent: 'warning',
  },
  Healthy: {
    iconName: 'successful_trend',
    iconName2: 'check_circle',
    subStatusIconName: 'done',
    iconColor: Colors.accentGreen(),
    textColor: Colors.textDefault(),
    text: 'Healthy',
    text2: 'Passing',
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
  [AssetHealthStatus.NOT_APPLICABLE]: STATUS_INFO['Not Applicable'],
  [AssetHealthStatus.UNKNOWN]: STATUS_INFO.Unknown,
  [AssetHealthStatus.DEGRADED]: STATUS_INFO.Degraded,
  [AssetHealthStatus.HEALTHY]: STATUS_INFO.Healthy,
  [AssetHealthStatus.WARNING]: STATUS_INFO.Warning,
};
