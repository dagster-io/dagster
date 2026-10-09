import {RunStatus} from '../../../graphql/types';
import {RunTimingCell} from '../RunTimingCell';
import {runEntry} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunTimingCell',
  component: RunTimingCell,
};

// Timed against the real clock so counters and relative text read as they do in the feed.
const NOW = Date.now() / 1000;
const MINUTE = 60;
const HOUR = 60 * MINUTE;

const waiting = {creationTime: NOW - 10 * MINUTE, startTime: null, endTime: null};

const runningFor = (seconds: number) => ({
  creationTime: NOW - seconds - MINUTE,
  startTime: NOW - seconds,
  endTime: null,
});

const finishedAfter = (seconds: number) => ({
  creationTime: NOW - HOUR - seconds - MINUTE,
  startTime: NOW - HOUR - seconds,
  endTime: NOW - HOUR,
});

const CellTemplate = ({entry}: {entry: MappedRunsFeedEntry}) => (
  <div
    style={{
      display: 'grid',
      gridTemplateColumns: '96px',
      alignItems: 'center',
      height: 48,
      padding: '0 16px',
      border: '1px solid var(--color-keyline-default)',
    }}
  >
    <RunTimingCell entry={entry} />
  </div>
);

export const NotStarted = () => (
  <CellTemplate entry={runEntry({runStatus: RunStatus.NOT_STARTED, ...waiting})} />
);
export const Starting = () => (
  <CellTemplate entry={runEntry({runStatus: RunStatus.STARTING, ...waiting})} />
);
export const Started = () => (
  <CellTemplate entry={runEntry({runStatus: RunStatus.STARTED, ...runningFor(2 * MINUTE + 14)})} />
);
export const Canceling = () => (
  <CellTemplate entry={runEntry({runStatus: RunStatus.CANCELING, ...runningFor(4 * MINUTE)})} />
);
export const Finished = () => (
  <CellTemplate
    entry={runEntry({runStatus: RunStatus.SUCCESS, ...finishedAfter(12 * MINUTE + 14)})}
  />
);
