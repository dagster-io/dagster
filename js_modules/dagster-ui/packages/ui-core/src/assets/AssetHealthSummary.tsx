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
} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';

import {asAssetKeyInput} from './asInput';
import {useAssetHealthData} from '../asset-data/AssetHealthDataProvider';
import {AssetHealthStatus} from '../graphql/types';

export const AssetHealthSummary = ({
  assetKey,
  iconOnly,
}: {
  assetKey: {path: string[]};
  iconOnly?: boolean;
}) => {
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
        <div>
          <Box padding={12} flex={{direction: 'row', alignItems: 'center', gap: 6}} border="bottom">
            {icon} <SubtitleLarge>{text}</SubtitleLarge>
          </Box>
          <Criteria
            text="Successfully materialized in last run"
            status={health?.materializationStatus}
          />
          <Criteria text="Has no freshness violations" status={health?.freshnessStatus} />
          <Criteria text="Has no check errors" status={health?.assetChecksStatus} />
        </div>
      }
    >
      {content()}
    </Popover>
  );
};

const Criteria = ({status, text}: {status: AssetHealthStatus | undefined; text: string}) => {
  const {subStatusIconName, iconColor, textColor} = statusToIconAndColor[status ?? 'undefined'];

  return (
    <Box
      padding={{horizontal: 12, vertical: 4}}
      flex={{direction: 'row', alignItems: 'center', gap: 6}}
    >
      <Icon name={subStatusIconName} color={iconColor} />
      <Body color={textColor}>{text}</Body>
    </Box>
  );
};

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
  }
> = {
  Unknown: {
    iconName: 'status',
    iconColor: Colors.textLight(),
    textColor: Colors.textDefault(),
    text: 'Unknown',
    intent: 'none',
    subStatusIconName: 'missing',
  },
  Degraded: {
    iconName: 'failure_trend',
    subStatusIconName: 'close',
    iconColor: Colors.accentRed(),
    textColor: Colors.textRed(),
    text: 'Degraded',
    intent: 'danger',
  },
  Warning: {
    iconName: 'warning_trend',
    subStatusIconName: 'close',
    iconColor: Colors.accentYellow(),
    text: 'Warning',
    textColor: Colors.textYellow(),
    intent: 'warning',
  },
  Healthy: {
    iconName: 'successful_trend',
    subStatusIconName: 'done',
    iconColor: Colors.accentGreen(),
    textColor: Colors.textDefault(),
    text: 'Healthy',
    intent: 'success',
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
