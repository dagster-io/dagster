import {Meta} from '@storybook/react';
import faker from 'faker';

import {RunStatus, buildPipelineTag, buildRun} from '../../graphql/types';
import {StorybookProvider} from '../../testing/StorybookProvider';
import {defaultMocks, hyphenatedName} from '../../testing/defaultMocks';
import {DagsterTag} from '../RunTag';
import {RunsFeedRow, RunsFeedTableHeader} from '../RunsFeedRowNew';

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

// Helper to create run with purely dynamic faker data plus specific launch type tags
const createRunWithDynamicTags = (specificTags: Array<{key: string; value: string}>) => {
  const fakerRun = defaultMocks.Run();
  const dynamicTags = fakerRun.tags();

  return buildRun({
    id: fakerRun.id(),
    jobName: fakerRun.jobName(),
    runStatus: fakerRun.runStatus,
    creationTime: fakerRun.creationTime,
    startTime: fakerRun.startTime,
    endTime: fakerRun.endTime,
    tags: [
      ...dynamicTags.map((tag) => buildPipelineTag({key: tag.key, value: tag.value})),
      ...specificTags.map((tag) => buildPipelineTag({key: tag.key, value: tag.value})),
    ],
  });
};

export const ManualRun = () => {
  const entry = createRunWithDynamicTags([{key: DagsterTag.User, value: faker.internet.email()}]);

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
    {key: DagsterTag.ScheduleName, value: `${hyphenatedName()}_schedule`},
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
    {key: DagsterTag.SensorName, value: `${hyphenatedName()}_sensor`},
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
    {key: DagsterTag.Backfill, value: faker.datatype.uuid().slice(0, 8)},
    {key: DagsterTag.User, value: faker.internet.email()},
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
    runStatus: fakerRun.runStatus,
    creationTime: fakerRun.creationTime,
    startTime: fakerRun.startTime,
    endTime: fakerRun.endTime,
    tags: fakerRun.tags().map((tag) => buildPipelineTag({key: tag.key, value: tag.value})),
  });

  return (
    <StorybookProvider>
      <RunRowWrapper>
        <RunsFeedRow entry={entry} />
      </RunRowWrapper>
    </StorybookProvider>
  );
};

// Additional status examples
export const CancelledRun = () => {
  const entry = createRunWithDynamicTags([{key: DagsterTag.User, value: faker.internet.email()}]);

  return (
    <StorybookProvider>
      <RunRowWrapper>
        <RunsFeedRow entry={entry} />
      </RunRowWrapper>
    </StorybookProvider>
  );
};

export const NotStartedRun = () => {
  const entry = createRunWithDynamicTags([
    {key: DagsterTag.ScheduleName, value: `${hyphenatedName()}_schedule`},
  ]);

  return (
    <StorybookProvider>
      <RunRowWrapper>
        <RunsFeedRow entry={entry} />
      </RunRowWrapper>
    </StorybookProvider>
  );
};

export const AllStatusesGrid = () => {
  const now = Date.now() / 1000;

  // Create one run for each status with appropriate timing
  const statusEntries = [
    {
      status: RunStatus.SUCCESS,
      entry: createRunWithDynamicTags([{key: DagsterTag.User, value: faker.internet.email()}]),
      timing: {startTime: now - 300, endTime: now - 60},
    },
    {
      status: RunStatus.STARTED,
      entry: createRunWithDynamicTags([
        {key: DagsterTag.ScheduleName, value: `${hyphenatedName()}_schedule`},
      ]),
      timing: {startTime: now - 180, endTime: null},
    },
    {
      status: RunStatus.FAILURE,
      entry: createRunWithDynamicTags([
        {key: DagsterTag.SensorName, value: `${hyphenatedName()}_sensor`},
      ]),
      timing: {startTime: now - 600, endTime: now - 540},
    },
    {
      status: RunStatus.QUEUED,
      entry: createRunWithDynamicTags([{key: DagsterTag.Automaterialize, value: 'true'}]),
      timing: {startTime: null, endTime: null},
    },
    {
      status: RunStatus.STARTING,
      entry: createRunWithDynamicTags([{key: DagsterTag.User, value: faker.internet.email()}]),
      timing: {startTime: null, endTime: null},
    },
    {
      status: RunStatus.NOT_STARTED,
      entry: createRunWithDynamicTags([
        {key: DagsterTag.ScheduleName, value: `${hyphenatedName()}_schedule`},
      ]),
      timing: {startTime: null, endTime: null},
    },
    {
      status: RunStatus.CANCELING,
      entry: createRunWithDynamicTags([{key: DagsterTag.User, value: faker.internet.email()}]),
      timing: {startTime: now - 120, endTime: null},
    },
    {
      status: RunStatus.CANCELED,
      entry: createRunWithDynamicTags([
        {key: DagsterTag.SensorName, value: `${hyphenatedName()}_sensor`},
      ]),
      timing: {startTime: now - 400, endTime: now - 380},
    },
  ];

  // Override the run status and timing for each entry
  const finalEntries = statusEntries.map(({status, entry, timing}) => ({
    ...entry,
    runStatus: status,
    startTime: timing.startTime,
    endTime: timing.endTime,
  }));

  return (
    <StorybookProvider>
      <div style={{display: 'grid', gridTemplateColumns: '1fr', gap: '1px', background: '#f0f0f0'}}>
        <RunsFeedTableHeader />
        {finalEntries.map((entry, index) => (
          <div key={index} style={{position: 'relative'}}>
            <div
              style={{
                position: 'absolute',
                left: '-120px',
                top: '50%',
                transform: 'translateY(-50%)',
                fontSize: '12px',
                fontWeight: 600,
                color: '#64748b',
                textAlign: 'right',
                width: '100px',
              }}
            >
              {statusEntries[index]?.status}
            </div>
            <RunsFeedRow entry={entry} />
          </div>
        ))}
      </div>
    </StorybookProvider>
  );
};
