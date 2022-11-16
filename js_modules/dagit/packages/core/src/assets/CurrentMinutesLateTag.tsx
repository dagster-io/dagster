import {Tooltip, Tag} from '@dagster-io/ui';
import moment from 'moment';
import React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';
import {AssetGraphLiveQuery_assetNodes_freshnessPolicy} from '../asset-graph/types/AssetGraphLiveQuery';
import {humanCronString} from '../schedules/humanCronString';

const STALE_OVERDUE_MSG = `A materialization incorporating more recent upstream data is overdue.`;
const STALE_UNMATERIALIZED_MSG = `This asset has never been materialized.`;

export const CurrentMinutesLateTag: React.FC<{
  liveData: LiveDataForNode;
  policyOnHover?: boolean;
}> = ({liveData, policyOnHover}) => {
  const {freshnessInfo, freshnessPolicy} = liveData;
  const description = policyOnHover ? freshnessPolicyDescription(freshnessPolicy) : '';

  if (!freshnessInfo) {
    return <span />;
  }

  if (freshnessInfo.currentMinutesLate === null) {
    return (
      <Tooltip
        content={<div style={{maxWidth: 400}}>{`${STALE_UNMATERIALIZED_MSG} ${description}`}</div>}
      >
        <Tag intent="danger">Late</Tag>
      </Tooltip>
    );
  }

  if (freshnessInfo.currentMinutesLate === 0) {
    return description ? (
      <Tooltip content={freshnessPolicyDescription(freshnessPolicy)}>
        <Tag intent="success">Fresh</Tag>
      </Tooltip>
    ) : (
      <Tag intent="success">Fresh</Tag>
    );
  }

  return (
    <Tooltip content={<div style={{maxWidth: 400}}>{`${STALE_OVERDUE_MSG} ${description}`}</div>}>
      <Tag intent="danger">
        {moment
          .duration(freshnessInfo.currentMinutesLate, 'minute')
          .humanize(false, {m: 120, h: 48})}
        {' late'}
      </Tag>
    </Tooltip>
  );
};

export const freshnessPolicyDescription = (
  freshnessPolicy: AssetGraphLiveQuery_assetNodes_freshnessPolicy | null,
) => {
  if (!freshnessPolicy) {
    return '';
  }

  const {cronSchedule, maximumLagMinutes} = freshnessPolicy;

  const cronDesc = cronSchedule ? humanCronString(cronSchedule, 'UTC').replace(/^At /, '') : '';
  const lagDesc =
    maximumLagMinutes % 30 === 0
      ? `${maximumLagMinutes / 60} hour${maximumLagMinutes / 60 !== 1 ? 's' : ''}`
      : `${maximumLagMinutes} min`;

  if (cronDesc) {
    return `By ${cronDesc}, this asset should incorporate all data up to ${lagDesc} before that time.`;
  } else {
    return `At any point in time, this asset should incorporate all data up to ${lagDesc} before that time.`;
  }
};
