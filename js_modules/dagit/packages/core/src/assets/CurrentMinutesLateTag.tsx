import {Tooltip, Tag} from '@dagster-io/ui';
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import relativeTime from 'dayjs/plugin/relativeTime';
import React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';
import {FreshnessPolicy} from '../graphql/types';
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
  `${dayjs.duration(minLate, 'minutes').humanize(false)} overdue`;

export const CurrentMinutesLateTag: React.FC<{
  liveData: LiveDataForNode | undefined;
  policy: FreshnessPolicy;
  policyOnHover?: boolean;
}> = ({liveData, policyOnHover, policy}) => {
  if (!liveData?.freshnessInfo) {
    return null;
  }

  const {freshnessInfo} = liveData;
  const description = policyOnHover ? freshnessPolicyDescription(policy) : '';

  if (freshnessInfo.currentMinutesLate === null) {
    return (
      <Tooltip
        content={<div style={{maxWidth: 400}}>{`${STALE_UNMATERIALIZED_MSG} ${description}`}</div>}
      >
        <Tag intent="danger" icon="warning">
          Overdue
        </Tag>
      </Tooltip>
    );
  }

  if (freshnessInfo.currentMinutesLate === 0) {
    return description ? (
      <Tooltip content={freshnessPolicyDescription(policy)}>
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

export const freshnessPolicyDescription = (freshnessPolicy: FreshnessPolicy | null) => {
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
    maximumLagMinutes % 30 === 0
      ? `${maximumLagMinutes / 60} hour${maximumLagMinutes / 60 !== 1 ? 's' : ''}`
      : `${maximumLagMinutes} min`;

  if (cronDesc) {
    return `By ${cronDesc}, this asset should incorporate all data up to ${lagDesc} before that${nbsp}time.`;
  } else {
    return `At any point in time, this asset should incorporate all data up to ${lagDesc} before that${nbsp}time.`;
  }
};
