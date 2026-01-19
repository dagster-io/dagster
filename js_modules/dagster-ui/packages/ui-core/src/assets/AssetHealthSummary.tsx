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
import {assetHealthEnabled} from 'shared/app/assetHealthEnabled.oss';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {useAllAssetsNodes} from './useAllAssets';
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
import {tokenForAssetKey} from '../asset-graph/Utils';
import {StatusCaseDot} from '../asset-graph/sidebar/util';
import {AssetHealthStatus, AssetKeyInput} from '../graphql/types';
import {TimeFromNow} from '../ui/TimeFromNow';
import {numberFormatter} from '../ui/formatters';

export const AssetHealthSummary = React.memo(
  ({assetKey, iconOnly}: {assetKey: {path: string[]}; iconOnly?: boolean}) => {
    if (!assetHealthEnabled()) {
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
          <HoverButton style={{padding: 8}}>
            <Icon name={iconName} color={iconColor} />
          </HoverButton>
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

  const {allAssetKeys, loading} = useAllAssetsNodes();

  function content() {
    if (!loading && !allAssetKeys.has(tokenForAssetKey(assetKey))) {
      // This asset is not in the workspace.
      return <Criteria assetKey={assetKey} status={health?.assetHealth} type="no-definition" />;
    }
    return (
      <>
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
      </>
    );
  }

  return (
    <Popover
      interactionKind="hover"
      content={
        <div onClick={(e) => e.stopPropagation()}>
          <Box padding={12} flex={{direction: 'row', alignItems: 'center', gap: 6}} border="bottom">
            <Icon name={iconName} color={iconColor} />
            <SubtitleLarge>{text}</SubtitleLarge>
          </Box>
          {content()}
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
    type: 'materialization' | 'freshness' | 'checks' | 'no-definition';
  }) => {
    const {subStatusIconName, iconColor, textColor} = statusToIconAndColor[status ?? 'undefined'];

    const trackEvent = useTrackEvent();
    const onClick = useCallback(
      (name: string) => () => {
        trackEvent('asset-health-summary-click', {name});
      },
      [trackEvent],
    );

    const derivedExplanation = useMemo(() => {
      if (type === 'no-definition') {
        return <Body>它可能已被删除或是通过集成导入的存根。</Body>;
      }

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
          return '无检查已执行';
        case 'AssetHealthCheckDegradedMeta':
          if (metadata.numWarningChecks > 0 && metadata.numFailedChecks > 0) {
            return (
              <Body>
                <Link
                  to={assetDetailsPathForKey(assetKey, {view: 'checks'})}
                  onClick={onClick('checks-degraded-all')}
                >
                  {numberFormatter.format(metadata.numWarningChecks)}/
                  {numberFormatter.format(metadata.totalNumChecks)} 个检查警告，{' '}
                  {numberFormatter.format(metadata.numFailedChecks)}/
                  {numberFormatter.format(metadata.totalNumChecks)} 个检查失败
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
                  {numberFormatter.format(metadata.totalNumChecks)} 个检查警告
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
                {numberFormatter.format(metadata.totalNumChecks)} 个检查失败
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
                {numberFormatter.format(metadata.totalNumChecks)} 个检查警告
              </Link>
            </Body>
          );
        case 'AssetHealthMaterializationDegradedNotPartitionedMeta':
          const toReturn = metadata.failedRunId ? (
            <Body>
              <Link
                to={`/runs/${metadata.failedRunId}`}
                onClick={onClick('materialization-degraded-not-partitioned')}
              >
                物化在运行 {metadata.failedRunId.split('-').shift()} 中失败
              </Link>
            </Body>
          ) : null;
          return toReturn;
        case 'AssetHealthMaterializationDegradedPartitionedMeta':
          return (
            <Body>
              <Link
                to={assetDetailsPathForKey(assetKey, {view: 'partitions', status: 'FAILED'})}
                onClick={onClick('degraded-partitioned')}
              >
                物化在 {numberFormatter.format(metadata.totalNumPartitions)} 个分区中的{' '}
                {numberFormatter.format(metadata.numFailedPartitions)} 个失败
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
                物化在 {numberFormatter.format(metadata.totalNumPartitions)} 个分区中的{' '}
                {numberFormatter.format(metadata.numMissingPartitions)} 个缺失
              </Link>
            </Body>
          );
        case 'AssetHealthFreshnessMeta':
          if (metadata.lastMaterializedTimestamp === null) {
            return <Body>无物化记录</Body>;
          }

          return (
            <Body>
              上次成功物化于{' '}
              <TimeFromNow unixTimestamp={Number(metadata.lastMaterializedTimestamp)} />
            </Body>
          );
        case undefined:
          return null;
        default:
          assertUnreachable(metadata);
      }
    }, [type, metadata, assetKey, onClick]);

    const {text, shouldDim} = useMemo(() => {
      switch (type) {
        case 'materialization':
          switch (status) {
            case AssetHealthStatus.DEGRADED:
              return {text: '执行失败', shouldDim: false};
            case AssetHealthStatus.HEALTHY:
              return {text: '执行成功', shouldDim: false};
            case AssetHealthStatus.WARNING:
              return {text: '执行警告', shouldDim: false};
            case undefined:
            case AssetHealthStatus.NOT_APPLICABLE:
              return {text: '无执行记录', shouldDim: true};
            case AssetHealthStatus.UNKNOWN:
              return {text: '执行状态未知', shouldDim: true};
            default:
              assertUnreachable(status);
          }
        case 'freshness':
          switch (status) {
            case AssetHealthStatus.HEALTHY:
              return {text: '新鲜度策略通过', shouldDim: false};
            case AssetHealthStatus.DEGRADED:
              return {text: '新鲜度策略失败', shouldDim: false};
            case AssetHealthStatus.WARNING:
              return {text: '新鲜度策略警告', shouldDim: false};
            case undefined:
            case AssetHealthStatus.NOT_APPLICABLE:
              return {text: '未定义新鲜度策略', shouldDim: true};
            case AssetHealthStatus.UNKNOWN:
              return {text: '新鲜度策略未评估', shouldDim: false};
            default:
              assertUnreachable(status);
          }
        case 'checks':
          switch (status) {
            case AssetHealthStatus.HEALTHY:
              return {text: '所有检查通过', shouldDim: false};
            case AssetHealthStatus.DEGRADED:
              if (metadata && 'numFailedChecks' in metadata && 'totalNumChecks' in metadata) {
                if (metadata.numFailedChecks === metadata.totalNumChecks) {
                  return {text: '所有检查失败', shouldDim: false};
                }
                return {text: '部分检查失败', shouldDim: false};
              }
              return {text: '检查失败', shouldDim: false};
            case AssetHealthStatus.WARNING:
              if (metadata && 'numWarningChecks' in metadata && 'totalNumChecks' in metadata) {
                if (metadata.numWarningChecks === metadata.totalNumChecks) {
                  return {text: '所有检查失败', shouldDim: false};
                }
              }
              return {text: '部分检查失败', shouldDim: false};
            case undefined:
            case AssetHealthStatus.NOT_APPLICABLE:
              return {text: '未定义检查', shouldDim: true};
            case AssetHealthStatus.UNKNOWN:
              return {text: '未评估检查', shouldDim: false};
            default:
              assertUnreachable(status);
          }
        case 'no-definition':
          return {
            text: `缺少软件定义`,
            shouldDim: false,
          };
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
          maxWidth: 300,
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
    materializationText: string;
  }
> = {
  'Not Applicable': {
    iconName: 'status',
    iconName2: 'missing',
    iconColor: Colors.textLight(),
    textColor: Colors.textDefault(),
    text: 'Unknown',
    text2: 'None set',
    materializationText: 'Not applicable',
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
    materializationText: 'Never materialized',
    subStatusIconName: 'missing',
    borderColor: Colors.accentGray(),
    backgroundColor: Colors.backgroundGray(),
    hoverBackgroundColor: Colors.backgroundGrayHover(),
  },
  Degraded: {
    iconName: 'failure_trend',
    iconName2: 'cancel',
    subStatusIconName: 'close',
    materializationText: 'Failed',
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
    materializationText: 'Not applicable',
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
    materializationText: 'Success',
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
