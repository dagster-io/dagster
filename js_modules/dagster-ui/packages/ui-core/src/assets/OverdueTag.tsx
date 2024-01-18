import {gql, useQuery} from '@apollo/client';
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import relativeTime from 'dayjs/plugin/relativeTime';
import React from 'react';

import {Box, Popover, Tag, Tooltip} from '@dagster-io/ui-components';

import {Timestamp} from '../app/time/Timestamp';
import {timestampToString} from '../app/time/timestampToString';
import {useAssetLiveData} from '../asset-data/AssetLiveDataProvider';
import {LiveDataForNode} from '../asset-graph/Utils';
import {AssetKeyInput, FreshnessPolicy} from '../graphql/types';
import {humanCronString} from '../schedules/humanCronString';
import {LoadingSpinner} from '../ui/Loading';
import {
  ASSET_MATERIALIZATION_UPSTREAM_TABLE_FRAGMENT,
  AssetMaterializationUpstreamTable,
  TimeSinceWithOverdueColor,
} from './AssetMaterializationUpstreamData';
import {OverduePopoverQuery, OverduePopoverQueryVariables} from './types/OverdueTag.types';

const STALE_UNMATERIALIZED_MSG = `This asset has never been materialized.`;
const locale = navigator.language;

dayjs.extend(duration);
dayjs.extend(relativeTime);

type LiveDataWithMinutesLate = LiveDataForNode & {
  freshnessInfo: NonNullable<LiveDataForNode['freshnessInfo']> & {currentMinutesLate: number};
};

export function isAssetOverdue(liveData?: LiveDataForNode): liveData is LiveDataWithMinutesLate {
  return (
    (liveData?.freshnessInfo && (liveData?.freshnessInfo.currentMinutesLate || 0) > 0) || false
  );
}

export const humanizedMinutesLateString = (minLate: number) =>
  dayjs.duration(minLate, 'minutes').humanize(false);

export const OverdueTag = ({
  policy,
  assetKey,
}: {
  policy: Pick<FreshnessPolicy, 'cronSchedule' | 'cronScheduleTimezone' | 'maximumLagMinutes'>;
  assetKey: AssetKeyInput;
}) => {
  const {liveData} = useAssetLiveData(assetKey);

  if (!liveData?.freshnessInfo) {
    return null;
  }

  const {freshnessInfo} = liveData;

  if (freshnessInfo.currentMinutesLate === null) {
    return (
      <Tooltip
        content={
          <div style={{maxWidth: 400}}>{`${STALE_UNMATERIALIZED_MSG} ${freshnessPolicyDescription(
            policy,
          )}`}</div>
        }
      >
        <Tag intent="danger" icon="warning">
          Overdue
        </Tag>
      </Tooltip>
    );
  }

  if (freshnessInfo.currentMinutesLate === 0) {
    return (
      <OverdueLineagePopover assetKey={assetKey} liveData={liveData}>
        <Tag intent="success" icon="check_circle" />
      </OverdueLineagePopover>
    );
  }

  return (
    <OverdueLineagePopover assetKey={assetKey} liveData={liveData}>
      <Tag intent="danger" icon="warning">
        {humanizedMinutesLateString(freshnessInfo.currentMinutesLate)} overdue
      </Tag>
    </OverdueLineagePopover>
  );
};

type OverdueLineagePopoverProps = {
  assetKey: AssetKeyInput;
  liveData: LiveDataForNode;
};

export const OverdueLineagePopover = ({
  children,
  assetKey,
  liveData,
}: OverdueLineagePopoverProps & {
  children: React.ReactNode;
}) => {
  return (
    <Popover
      position="top"
      interactionKind="hover"
      className="chunk-popover-target"
      content={
        <OverdueLineagePopoverContent
          assetKey={assetKey}
          timestamp={liveData.lastMaterialization?.timestamp || ''}
        />
      }
    >
      {children}
    </Popover>
  );
};

const OverdueLineagePopoverContent = ({
  assetKey,
  timestamp,
}: {
  assetKey: AssetKeyInput;
  timestamp: string;
}) => {
  const result = useQuery<OverduePopoverQuery, OverduePopoverQueryVariables>(
    OVERDUE_POPOVER_QUERY,
    {variables: {assetKey: {path: assetKey.path}, timestamp}},
  );

  const data =
    result.data?.assetNodeOrError.__typename === 'AssetNode' ? result.data.assetNodeOrError : null;

  if (!data) {
    return (
      <Box style={{width: 600}}>
        <LoadingSpinner purpose="section" />
      </Box>
    );
  }

  if (!data.freshnessInfo || !data.freshnessPolicy?.lastEvaluationTimestamp) {
    return <Box style={{width: 600}}>No freshness policy or evaluation timestamp.</Box>;
  }

  const hasUpstreams = data.assetMaterializationUsedData.length > 0;
  const {currentLagMinutes, currentMinutesLate} = data.freshnessInfo;
  const {lastEvaluationTimestamp, cronSchedule, cronScheduleTimezone, maximumLagMinutes} =
    data.freshnessPolicy;
  const maxLagMinutesStr = humanizedMinutesLateString(maximumLagMinutes);
  const lagMinutesStr = humanizedMinutesLateString(currentLagMinutes || 0);
  const derivedStr = hasUpstreams ? ` is derived from source data that` : '';
  const policyStr = freshnessPolicyDescription(data.freshnessPolicy, 'short');

  const lastEvaluationStr = timestampToString({
    locale,
    timezone: cronScheduleTimezone || 'UTC',
    timestamp: {ms: Number(lastEvaluationTimestamp)},
    timeFormat: {showTimezone: true},
  });

  return (
    <Box style={{width: 600}}>
      <Box padding={12} border="bottom">
        {currentMinutesLate === 0 // fresh
          ? cronSchedule
            ? `The latest materialization contains all data up to ${maxLagMinutesStr} before ${lastEvaluationStr}. `
            : `The latest materialization${derivedStr} is ${lagMinutesStr} old. `
          : cronSchedule
          ? `The latest materialization${derivedStr} was ${lagMinutesStr} old on ${lastEvaluationStr}. `
          : `The latest materialization${derivedStr} is ${lagMinutesStr} old. `}

        {hasUpstreams
          ? `The asset's freshness policy requires it to be derived from data ${policyStr}`
          : `The asset's freshness policy requires it is ${policyStr}`}
      </Box>
      {hasUpstreams ? (
        <>
          <Box padding={12} style={{fontWeight: 600}}>
            Latest materialization sources data from:
          </Box>
          <Box
            style={{maxHeight: '240px', overflowY: 'auto', marginLeft: -1, marginRight: -1}}
            onClick={(e) => e.stopPropagation()}
          >
            <AssetMaterializationUpstreamTable
              data={data}
              maximumLagMinutes={data.freshnessPolicy.maximumLagMinutes}
              relativeTo={cronSchedule ? Number(lastEvaluationTimestamp) : 'now'}
              assetKey={assetKey}
            />
          </Box>
        </>
      ) : (
        <>
          <Box padding={12} style={{fontWeight: 600}} border="bottom">
            Latest materialization:
          </Box>
          <Box padding={12} flex={{justifyContent: 'space-between'}} border="bottom">
            <Timestamp timestamp={{ms: Number(timestamp)}} />
            <TimeSinceWithOverdueColor
              timestamp={Number(timestamp)}
              relativeTo={cronSchedule ? Number(lastEvaluationTimestamp) : 'now'}
              maximumLagMinutes={data.freshnessPolicy.maximumLagMinutes}
            />
          </Box>
        </>
      )}
    </Box>
  );
};

export const freshnessPolicyDescription = (
  freshnessPolicy: Pick<
    FreshnessPolicy,
    'cronSchedule' | 'cronScheduleTimezone' | 'maximumLagMinutes'
  > | null,
  format: 'long' | 'short' = 'long',
) => {
  if (!freshnessPolicy) {
    return '';
  }

  const {cronSchedule, maximumLagMinutes, cronScheduleTimezone} = freshnessPolicy;
  const nbsp = '\xa0';
  const cronDesc = cronSchedule
    ? humanCronString(cronSchedule, cronScheduleTimezone ? cronScheduleTimezone : 'UTC').replace(
        /^At /,
        '',
      )
    : '';
  const lagDesc =
    maximumLagMinutes % (24 * 60) === 0
      ? `${maximumLagMinutes / (24 * 60)} day${maximumLagMinutes / (24 * 60) !== 1 ? 's' : ''}`
      : maximumLagMinutes % 30 === 0
      ? `${maximumLagMinutes / 60} hour${maximumLagMinutes / 60 !== 1 ? 's' : ''}`
      : `${maximumLagMinutes} min`;

  if (format === 'short') {
    if (cronDesc) {
      return `no more than ${lagDesc} old by${nbsp}${cronDesc}.`;
    } else {
      return `no more than ${lagDesc} old at any${nbsp}time.`;
    }
  } else {
    if (cronDesc) {
      return `By ${cronDesc}, this asset should incorporate all data up to ${lagDesc} before that${nbsp}time.`;
    } else {
      return `At any point in time, this asset should incorporate all data up to ${lagDesc} before that${nbsp}time.`;
    }
  }
};

export const OVERDUE_POPOVER_QUERY = gql`
  query OverduePopoverQuery($assetKey: AssetKeyInput!, $timestamp: String!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        freshnessInfo {
          currentLagMinutes
          currentMinutesLate
        }
        freshnessPolicy {
          __typename
          cronSchedule
          cronScheduleTimezone
          lastEvaluationTimestamp
          maximumLagMinutes
        }
        ...AssetMaterializationUpstreamTableFragment
      }
    }
  }
  ${ASSET_MATERIALIZATION_UPSTREAM_TABLE_FRAGMENT}
`;
