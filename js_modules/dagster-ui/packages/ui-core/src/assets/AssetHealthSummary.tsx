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

import {gql, useQuery} from '../apollo-client';
import {asAssetKeyInput} from './asInput';
import {assertUnreachable} from '../app/Util';
import {AssetHealthStatus} from '../graphql/types';
import {GetAssetHealthQuery, GetAssetHealthQueryVariables} from './types/AssetHealthSummary.types';

export const AssetHealthSummary = ({
  assetKey,
  iconOnly,
}: {
  assetKey: {path: string[]};
  iconOnly?: boolean;
}) => {
  const key = useMemo(() => asAssetKeyInput(assetKey), [assetKey]);

  const {data: healthData, loading: healthDataLoading} = useQuery<
    GetAssetHealthQuery,
    GetAssetHealthQueryVariables
  >(GET_ASSET_HEALTH_QUERY, {
    variables: {
      assetKey: key,
    },
  });

  const health = healthData?.assetNodes[0]?.assetHealth;
  const {iconName, iconColor, intent, text} = useMemo(() => {
    return statusToIconAndColor(health?.assetHealth);
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

  if (healthDataLoading && !healthData) {
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
  const {subStatusIconName, iconColor, textColor} = statusToIconAndColor(status);

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

const GET_ASSET_HEALTH_QUERY = gql`
  query GetAssetHealth($assetKey: AssetKeyInput!) {
    assetNodes(assetKeys: [$assetKey]) {
      id
      assetHealth {
        assetHealth
        materializationStatus
        assetChecksStatus
        freshnessStatus
      }
    }
  }
`;

function statusToIconAndColor(status: AssetHealthStatus | undefined): {
  iconName: IconName;
  subStatusIconName: IconName;
  iconColor: string;
  textColor: string;
  text: string;
  intent: Intent;
} {
  switch (status) {
    case undefined:
    case AssetHealthStatus.NOT_APPLICABLE:
    case AssetHealthStatus.UNKNOWN:
      return {
        iconName: 'status',
        iconColor: Colors.textLight(),
        textColor: Colors.textDefault(),
        text: 'Unknown',
        intent: 'none',
        subStatusIconName: 'missing',
      };
    case AssetHealthStatus.DEGRADED:
      return {
        iconName: 'failure_trend',
        subStatusIconName: 'close',
        iconColor: Colors.accentRed(),
        textColor: Colors.textRed(),
        text: 'Degraded',
        intent: 'danger',
      };
    case AssetHealthStatus.HEALTHY:
      return {
        iconName: 'successful_trend',
        subStatusIconName: 'done',
        iconColor: Colors.accentGreen(),
        textColor: Colors.textDefault(),
        text: 'Healthy',
        intent: 'success',
      };
    case AssetHealthStatus.WARNING:
      return {
        iconName: 'warning_trend',
        subStatusIconName: 'close',
        iconColor: Colors.accentYellow(),
        text: 'Warning',
        textColor: Colors.textYellow(),
        intent: 'warning',
      };
    default:
      assertUnreachable(status);
  }
}
