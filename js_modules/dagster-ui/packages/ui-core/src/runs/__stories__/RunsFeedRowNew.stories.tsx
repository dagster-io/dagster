import {Meta} from '@storybook/react';

import {RunStatus, buildRun} from '../../graphql/types';
import {StorybookProvider} from '../../testing/StorybookProvider';
import {DagsterTag} from '../RunTag';
import {RunsFeedRow, RunsFeedTableHeader} from '../RunsFeedRowNew';
import {defaultMocks} from '../../testing/defaultMocks';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunsFeedRowNew',
  component: RunsFeedRow,
} as Meta;

const RunRowWrapper = ({children}: {children: React.ReactNode}) => (
  <div style={{display: 'grid', gridTemplateColumns: '1fr', gap: '1px', background: '#f0f0f0'}}>
    <RunsFeedTableHeader />
    {children}
  </div>
);

// Helper to create run with dynamic faker tags plus specific overrides
const createRunWithDynamicTags = (specificTags: Array<{key: string; value: string}>) => {
  const fakerRun = defaultMocks.Run();
  const dynamicTags = fakerRun.tags();
  
  return buildRun({
    id: fakerRun.id(),
    jobName: fakerRun.jobName(),
    runStatus: RunStatus.SUCCESS,
    creationTime: Date.now() / 1000 - Math.random() * 7200, // Random time in last 2 hours
    tags: [
      ...dynamicTags.map((tag) => ({key: tag.key, value: tag.value})),
      ...specificTags,
    ],
  });
};

export const ManualRun = () => {
  const entry = createRunWithDynamicTags([
    {key: DagsterTag.User, value: 'john.doe@example.com'},
  ]);

  return (
    <StorybookProvider>
      <RunRowWrapper>
        <RunsFeedRow entry={entry} />
      </RunRowWrapper>
    </StorybookProvider>
  );
};

export const ScheduledRun = () => {
  const entry = createRunWithDynamicTags([
    {key: DagsterTag.ScheduleName, value: 'daily_etl_schedule'},
  ]);

  return (
    <StorybookProvider>
      <RunRowWrapper>
        <RunsFeedRow entry={entry} />
      </RunRowWrapper>
    </StorybookProvider>
  );
};

export const SensorRun = () => {
  const entry = createRunWithDynamicTags([
    {key: DagsterTag.SensorName, value: 's3_file_sensor'},
  ]);

  return (
    <StorybookProvider>
      <RunRowWrapper>
        <RunsFeedRow entry={entry} />
      </RunRowWrapper>
    </StorybookProvider>
  );
};

export const DeclarativeAutomation = () => {
  const entry = createRunWithDynamicTags([
    {key: DagsterTag.Automaterialize, value: 'true'},
    {key: DagsterTag.AutomationCondition, value: 'true'},
    {key: DagsterTag.SensorName, value: 'default_automation_condition_sensor'},
  ]);

  return (
    <StorybookProvider>
      <RunRowWrapper>
        <RunsFeedRow entry={entry} />
      </RunRowWrapper>
    </StorybookProvider>
  );
};

export const BackfillLaunchedRun = () => {
  const entry = createRunWithDynamicTags([
    {key: DagsterTag.Backfill, value: 'fwfelkfm'},
    {key: DagsterTag.User, value: 'anil@dagsterlabs.com'},
  ]);

  return (
    <StorybookProvider>
      <RunRowWrapper>
        <RunsFeedRow entry={entry} />
      </RunRowWrapper>
    </StorybookProvider>
  );
};

export const PurelyDynamicRun = () => {
  const fakerRun = defaultMocks.Run();
  const entry = buildRun({
    id: fakerRun.id(),
    jobName: fakerRun.jobName(),
    runStatus: RunStatus.SUCCESS,
    creationTime: Date.now() / 1000 - Math.random() * 7200,
    tags: fakerRun.tags().map((tag) => ({key: tag.key, value: tag.value})),
  });

  return (
    <StorybookProvider>
      <RunRowWrapper>
        <RunsFeedRow entry={entry} />
      </RunRowWrapper>
    </StorybookProvider>
  );
};