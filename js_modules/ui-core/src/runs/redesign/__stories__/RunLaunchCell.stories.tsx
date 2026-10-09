import {showToast} from '@dagster-io/ui-components';

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
  scheduleRun,
  sensorRun,
  singlePartitionRun,
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
