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
import React, {useMemo} from 'react';
import {Link} from 'react-router-dom';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {featureEnabled} from '../app/Flags';
import {assertUnreachable} from '../app/Util';
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
    if (!featureEnabled(FeatureFlag.flagUseNewObserveUIs)) {
      return null;
    }

    return <AssetHealthSummaryImpl assetKey={assetKey} iconOnly={iconOnly} />;
  },
);

const AssetHealthSummaryImpl = React.memo(
  ({assetKey, iconOnly}: {assetKey: {path: string[]}; iconOnly?: boolean}) => {
    const {liveData} = useAssetHealthData(assetKey);
    const health = liveData?.assetHealth;

    const {iconName, iconColor, intent, text} = useMemo(() => {
      return statusToIconAndColor[health?.assetHealth ?? 'undefined'];
    }, [health]);

    function content() {
      if (iconOnly) {
        return (
          <UnstyledButton style={{display: 'flex', alignItems: 'center', padding: 8}}>
            <Icon name={iconName} color={iconColor} />
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
  const {iconName, iconColor, text} = useMemo(() => {
    return statusToIconAndColor[health?.assetHealth ?? 'undefined'];
  }, [health]);

  return (
    <Popover
      interactionKind="hover"
      content={
        <div onClick={(e) => e.stopPropagation()}>
          <Box padding={12} flex={{direction: 'row', alignItems: 'center', gap: 6}} border="bottom">
            <Icon name={iconName} color={iconColor} />
            <SubtitleLarge>{text}</SubtitleLarge>
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
    const {subStatusIconName, iconColor, textColor} = statusToIconAndColor[status ?? 'undefined'];

    const derivedExplanation = useMemo(() => {
      switch (metadata?.__typename) {
        case 'AssetHealthCheckUnknownMeta':
          if (metadata.numNotExecutedChecks > 0) {
            return (
              <Body>
                <Link to={assetDetailsPathForKey(assetKey, {view: 'checks'})}>
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
                <Link to={assetDetailsPathForKey(assetKey, {view: 'checks'})}>
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
              <Link to={assetDetailsPathForKey(assetKey, {view: 'partitions', status: 'FAILED'})}>
                Materialization failed in {numberFormatter.format(metadata.numFailedPartitions)} out
                of {numberFormatter.format(metadata.totalNumPartitions)} partition
                {ifPlural(metadata.totalNumPartitions, '', 's')}
              </Link>
            </Body>
          );
        case 'AssetHealthMaterializationHealthyPartitionedMeta':
          return (
            <Body>
              <Link to={assetDetailsPathForKey(assetKey, {view: 'partitions', status: 'MISSING'})}>
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
              Last materialized{' '}
              <TimeFromNow unixTimestamp={Number(metadata.lastMaterializedTimestamp)} />
            </Body>
          );
        case undefined:
          return null;
        default:
          assertUnreachable(metadata);
      }
    }, [metadata, assetKey]);

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
        <Icon name={subStatusIconName} color={iconColor} style={{paddingTop: 2}} />
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
    iconName: IconName;
    iconName2: IconName;
    subStatusIconName: IconName;
    iconColor: string;
    textColor: string;
    borderColor: string;
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
    borderColor: Colors.accentGray(),
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
    borderColor: Colors.accentGray(),
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
    text2: 'Failed',
    intent: 'danger',
    borderColor: Colors.accentRed(),
    backgroundColor: Colors.backgroundRed(),
    hoverBackgroundColor: Colors.backgroundRedHover(),
  },
  Warning: {
    iconName: 'warning_trend',
    iconName2: 'warning_outline',
    subStatusIconName: 'warning_outline',
    iconColor: Colors.accentYellow(),
    text: 'Warning',
    text2: 'Warning',
    textColor: Colors.textYellow(),
    borderColor: Colors.accentYellow(),
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
