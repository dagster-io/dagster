import {Colors} from '@dagster-io/ui';

import {queuedStatuses, inProgressStatuses, failedStatuses, successStatuses} from './RunStatuses';
import {TimelineRun} from './RunTimeline';

type BackgroundStatus = 'inProgress' | 'queued' | 'failed' | 'succeeded' | 'scheduled';

const statusToColor = (status: BackgroundStatus) => {
  switch (status) {
    case 'queued':
      return Colors.Blue200;
    case 'inProgress':
      return Colors.Blue500;
    case 'failed':
      return Colors.Red500;
    case 'succeeded':
      return Colors.Green500;
    case 'scheduled':
      return Colors.Blue200;
  }
};

export const mergeStatusToBackground = (runs: TimelineRun[]) => {
  const counts = {
    scheduled: 0,
    queued: 0,
    inProgress: 0,
    failed: 0,
    succeeded: 0,
  };

  runs.forEach(({status}) => {
    if (status === 'SCHEDULED') {
      counts.scheduled++;
    } else if (queuedStatuses.has(status)) {
      counts.queued++;
    } else if (inProgressStatuses.has(status)) {
      counts.inProgress++;
    } else if (failedStatuses.has(status)) {
      counts.failed++;
    } else if (successStatuses.has(status)) {
      counts.succeeded++;
    }
  });

  const statusArr = Object.keys(counts).filter(
    (status) => counts[status] > 0,
  ) as BackgroundStatus[];

  if (statusArr.length === 1) {
    const [element] = statusArr;
    return statusToColor(element);
  }

  // const colorList = statusArr.map(statusToColor);
  const runCount = runs.length;

  const colors = [
    counts.failed > 0 ? {status: 'failed', pct: (counts.failed * 100) / runCount} : null,
    counts.succeeded > 0 ? {status: 'succeeded', pct: (counts.succeeded * 100) / runCount} : null,
    counts.inProgress > 0
      ? {status: 'inProgress', pct: (counts.inProgress * 100) / runCount}
      : null,
    counts.queued > 0 ? {status: 'queued', pct: (counts.queued * 100) / runCount} : null,
    counts.scheduled > 0 ? {status: 'scheduled', pct: (counts.scheduled * 100) / runCount} : null,
  ].filter(Boolean);

  let colorString = '';
  let nextPct = 0;
  let pctSoFar = 0;

  for (let ii = 0; ii < colors.length; ii++) {
    const value = colors[ii];
    if (!value) {
      continue;
    }

    const {status, pct} = value;
    pctSoFar = nextPct;
    nextPct += pct;
    const colorForStatus = statusToColor(status as BackgroundStatus);
    if (ii === 0) {
      colorString += `${colorForStatus} ${pct.toFixed(1)}%, `;
    } else if (ii === colors.length - 1) {
      colorString += `${colorForStatus} ${pctSoFar.toFixed(1)}%`;
    } else {
      colorString += `${colorForStatus} ${pctSoFar.toFixed(1)}% ${nextPct.toFixed(1)}%, `;
    }
  }

  return `linear-gradient(to right, ${colorString})`;
};
