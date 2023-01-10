import {Tooltip, Tag} from '@dagster-io/ui';
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import relativeTime from 'dayjs/plugin/relativeTime';
import React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';
import {AssetNodeLiveFreshnessPolicyFragment} from '../graphql/graphql';
import {humanCronString} from '../schedules/humanCronString';

const STALE_OVERDUE_MSG = `A materialization incorporating more recent upstream data is overdue.`;
const STALE_UNMATERIALIZED_MSG = `This asset has never been materialized.`;

dayjs.extend(duration);
dayjs.extend(relativeTime);

type LiveDataWithMinutesLate = LiveDataForNode & {
  freshnessInfo: NonNullable<LiveDataForNode['freshnessInfo']> & {currentMinutesLate: number};
};

export function isAssetLate(liveData?: LiveDataForNode): liveData is LiveDataWithMinutesLate {
  return (
    (liveData?.freshnessInfo && (liveData?.freshnessInfo.currentMinutesLate || 0) > 0) || false
  );
}

export const humanizedLateString = (minLate: number) =>
  `${dayjs.duration(minLate, 'minutes').humanize(false)} late`;

export const CurrentMinutesLateTag: React.FC<{
  liveData: LiveDataForNode;
  policyOnHover?: boolean;
}> = ({liveData, policyOnHover}) => {
  const {freshnessInfo, freshnessPolicy} = liveData;
  const description = policyOnHover ? freshnessPolicyDescription(freshnessPolicy) : '';

  if (!freshnessInfo) {
    return null;
  }

  if (freshnessInfo.currentMinutesLate === null) {
    return (
      <Tooltip
        content={<div style={{maxWidth: 400}}>{`${STALE_UNMATERIALIZED_MSG} ${description}`}</div>}
      >
        <Tag intent="danger" icon="warning">
          Late
        </Tag>
      </Tooltip>
    );
  }

  if (freshnessInfo.currentMinutesLate === 0) {
    return description ? (
      <Tooltip content={freshnessPolicyDescription(freshnessPolicy)}>
        <Tag intent="success" icon="check_circle" />
      </Tooltip>
    ) : (
      <Tag intent="success" icon="check_circle" />
    );
  }

  return (
    <Tooltip content={<div style={{maxWidth: 400}}>{`${STALE_OVERDUE_MSG} ${description}`}</div>}>
      <Tag intent="danger" icon="warning">
        {humanizedLateString(freshnessInfo.currentMinutesLate)}
      </Tag>
    </Tooltip>
  );
};

export const freshnessPolicyDescription = (
  freshnessPolicy: AssetNodeLiveFreshnessPolicyFragment | null,
) => {
  if (!freshnessPolicy) {
    return '';
  }

  const {cronSchedule, maximumLagMinutes} = freshnessPolicy;
  const nbsp = '\xa0';
  const cronDesc = cronSchedule ? humanCronString(cronSchedule, 'UTC').replace(/^At /, '') : '';
  const lagDesc =
    maximumLagMinutes % 30 === 0
      ? `${maximumLagMinutes / 60} hour${maximumLagMinutes / 60 !== 1 ? 's' : ''}`
      : `${maximumLagMinutes} min`;

  if (cronDesc) {
    return `By ${cronDesc}, this asset should incorporate all data up to ${lagDesc} before that${nbsp}time.`;
  } else {
    return `At any point in time, this asset should incorporate all data up to ${lagDesc} before that${nbsp}time.`;
  }
};
