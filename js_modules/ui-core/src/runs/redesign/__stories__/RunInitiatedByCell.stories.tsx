import {showToast} from '@dagster-io/ui-components';

import {RunInitiatedByCell} from '../RunInitiatedByCell';
import {
  autoObserveRun,
  autoRetryInBackfillRun,
  backfillChildRun,
  defaultAutomationSensorRun,
  manualRun,
  manualRunWithUser,
  namedAutomationSensorRun,
  reExecutionRun,
  scheduleRun,
  scheduleRunWithTick,
  sensorRun,
} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunInitiatedByCell',
  component: RunInitiatedByCell,
};

const CellTemplate = ({entry}: {entry: MappedRunsFeedEntry}) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      // Fixed-width so cell truncation is visible
      width: 420,
      height: 48,
      padding: '0 16px',
      border: '1px solid var(--color-keyline-default)',
    }}
  >
    <RunInitiatedByCell
      entry={entry}
      onOpenTickDetails={() => {
        showToast({message: 'The tick dialog opens here.', intent: 'none'});
      }}
    />
  </div>
);

export const Schedule = () => <CellTemplate entry={scheduleRun} />;
export const ScheduleWithTick = () => <CellTemplate entry={scheduleRunWithTick} />;
export const Sensor = () => <CellTemplate entry={sensorRun} />;
export const DeclarativeAutomation = () => <CellTemplate entry={defaultAutomationSensorRun} />;
export const NamedAutomationSensor = () => <CellTemplate entry={namedAutomationSensorRun} />;
export const AutoObservation = () => <CellTemplate entry={autoObserveRun} />;
export const Backfill = () => <CellTemplate entry={backfillChildRun} />;
export const Manual = () => <CellTemplate entry={manualRun} />;
export const ManualWithUser = () => <CellTemplate entry={manualRunWithUser} />;
export const ReExecution = () => <CellTemplate entry={reExecutionRun} />;
export const AutoRetryInsideBackfill = () => <CellTemplate entry={autoRetryInBackfillRun} />;
