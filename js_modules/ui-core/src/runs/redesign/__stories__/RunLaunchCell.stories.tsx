import {showToast} from '@dagster-io/ui-components';
import {ComponentType, useEffect, useState} from 'react';

import {RunLaunchCell} from '../RunLaunchCell';
import {
  autoObserveRun,
  autoRetryInBackfillRun,
  backfillChildRun,
  completeSelectionRun,
  defaultAutomationSensorRun,
  jobBackfill,
  manualRun,
  manualRunWithUser,
  partitionRangeRun,
  partitionSetBackfill,
  reExecutionRun,
  runEntry,
  scheduleRun,
  sensorRun,
  singlePartitionRun,
  tag,
} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunLaunchCell',
  component: RunLaunchCell,
};

const CellTemplate = ({entry}: {entry: MappedRunsFeedEntry}) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      width: 420,
      height: 48,
      padding: '0 16px',
      border: '1px solid var(--color-keyline-default)',
    }}
  >
    <RunLaunchCell
      entry={entry}
      onOpenTickDetails={() => {
        showToast({message: 'The tick dialog opens here.', intent: 'none'});
      }}
    />
  </div>
);

export const Schedule = () => <CellTemplate entry={scheduleRun} />;
export const Sensor = () => <CellTemplate entry={sensorRun} />;
export const DeclarativeAutomation = () => <CellTemplate entry={defaultAutomationSensorRun} />;
export const AutoObservation = () => <CellTemplate entry={autoObserveRun} />;
export const Backfill = () => <CellTemplate entry={backfillChildRun} />;
export const Manual = () => <CellTemplate entry={manualRun} />;
export const ManualWithUser = () => <CellTemplate entry={manualRunWithUser} />;
export const Job = () => <CellTemplate entry={completeSelectionRun} />;
export const SinglePartition = () => <CellTemplate entry={singlePartitionRun} />;
export const PartitionRange = () => <CellTemplate entry={partitionRangeRun} />;
export const JobBackfill = () => <CellTemplate entry={jobBackfill} />;
export const PartitionSetBackfill = () => <CellTemplate entry={partitionSetBackfill} />;
export const ReExecution = () => <CellTemplate entry={reExecutionRun} />;
export const AutomaticRetryInsideBackfill = () => <CellTemplate entry={autoRetryInBackfillRun} />;

const RUN_TAGS = [
  {key: 'team', value: 'data'},
  {key: 'dagster/run_key', value: 'nightly'},
  {
    key: 'description',
    value: 'Nightly refresh of the sales and inventory marts after the warehouse export completes',
  },
];

export const VisibleTags = () => (
  <CellTemplate
    entry={runEntry({
      jobName: 'daily_etl',
      tags: RUN_TAGS.map(({key, value}) => tag(key, value)),
    })}
  />
);

const PINNED_TAGS_STORAGE_KEY = 'pinned-run-tags';

// Seeds the pinned tags before the first render and restores the viewer's own afterwards.
const WithPinnedTags = (Story: ComponentType) => {
  const [previous] = useState(() => {
    const stored = window.localStorage.getItem(PINNED_TAGS_STORAGE_KEY);
    window.localStorage.setItem(
      PINNED_TAGS_STORAGE_KEY,
      JSON.stringify(RUN_TAGS.map(({key}) => key)),
    );
    return stored;
  });

  useEffect(
    () => () => {
      if (previous === null) {
        window.localStorage.removeItem(PINNED_TAGS_STORAGE_KEY);
      } else {
        window.localStorage.setItem(PINNED_TAGS_STORAGE_KEY, previous);
      }
    },
    [previous],
  );

  return <Story />;
};

VisibleTags.decorators = [WithPinnedTags];
