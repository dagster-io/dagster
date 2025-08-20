import {Meta} from '@storybook/react';

import {RunStatus, buildPipelineTag, buildRun} from '../../graphql/types';
import {StorybookProvider} from '../../testing/StorybookProvider';
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

// Manual run launched by a user
export const ManualRun = () => {
  const entry = buildRun({
    runStatus: RunStatus.SUCCESS,
    id: 'manual-run-123',
    jobName: 'my_data_pipeline',
    tags: [buildPipelineTag({key: DagsterTag.User, value: 'alice@company.com'})],
  });
  return (
    <StorybookProvider>
      <RunRowWrapper>
        <RunsFeedRow entry={entry} />
      </RunRowWrapper>
    </StorybookProvider>
  );
};

// Scheduled run
export const ScheduledRun = () => {
  const entry = buildRun({
    runStatus: RunStatus.SUCCESS,
    id: 'scheduled-run-456',
    jobName: 'daily_etl_job',
    tags: [buildPipelineTag({key: DagsterTag.ScheduleName, value: 'daily_etl_schedule'})],
  });
  return (
    <StorybookProvider>
      <RunRowWrapper>
        <RunsFeedRow entry={entry} />
      </RunRowWrapper>
    </StorybookProvider>
  );
};

// Sensor-triggered run
export const SensorRun = () => {
  const entry = buildRun({
    runStatus: RunStatus.STARTED,
    id: 'sensor-run-789',
    jobName: 'file_processing_job',
    tags: [buildPipelineTag({key: DagsterTag.SensorName, value: 's3_file_sensor'})],
  });
  return (
    <StorybookProvider>
      <RunRowWrapper>
        <RunsFeedRow entry={entry} />
      </RunRowWrapper>
    </StorybookProvider>
  );
};

// Run launched by a backfill
export const BackfillLaunchedRun = () => {
  const entry = buildRun({
    runStatus: RunStatus.SUCCESS,
    id: '97ddc9fd-5f96-4a62-8395-76d514ed47e9',
    jobName: '__ASSET_JOB',
    tags: [
      buildPipelineTag({key: DagsterTag.Backfill, value: 'fwfelkfm'}),
      buildPipelineTag({key: DagsterTag.User, value: 'anil@dagsterlabs.com'}),
    ],
  });
  return (
    <StorybookProvider>
      <RunRowWrapper>
        <RunsFeedRow entry={entry} />
      </RunRowWrapper>
    </StorybookProvider>
  );
};

// Declarative automation run
export const DeclarativeAutomationRun = () => {
  const entry = buildRun({
    runStatus: RunStatus.SUCCESS,
    id: 'automation-run-101',
    jobName: '__ASSET_JOB',
    tags: [
      buildPipelineTag({key: DagsterTag.Automaterialize, value: 'true'}),
      buildPipelineTag({key: DagsterTag.AutomationCondition, value: 'true'}),
      buildPipelineTag({key: DagsterTag.SensorName, value: 'default_automation_condition_sensor'}),
    ],
  });
  return (
    <StorybookProvider>
      <RunRowWrapper>
        <RunsFeedRow entry={entry} />
      </RunRowWrapper>
    </StorybookProvider>
  );
};

// All examples together with different creation times
export const AllLaunchTypes = () => {
  const now = Date.now() / 1000;
  const runs = [
    buildRun({
      runStatus: RunStatus.SUCCESS,
      id: 'manual-1',
      jobName: 'user_pipeline',
      creationTime: now - 30, // 30 seconds ago
      tags: [buildPipelineTag({key: DagsterTag.User, value: 'alice@company.com'})],
    }),
    buildRun({
      runStatus: RunStatus.SUCCESS,
      id: 'scheduled-1',
      jobName: 'daily_job',
      creationTime: now - 300, // 5 minutes ago
      tags: [buildPipelineTag({key: DagsterTag.ScheduleName, value: 'daily_schedule'})],
    }),
    buildRun({
      runStatus: RunStatus.STARTED,
      id: 'sensor-1',
      jobName: 'reactive_job',
      creationTime: now - 7200, // 2 hours ago
      tags: [buildPipelineTag({key: DagsterTag.SensorName, value: 'file_sensor'})],
    }),
    buildRun({
      runStatus: RunStatus.SUCCESS,
      id: 'backfill-1',
      jobName: '__ASSET_JOB',
      creationTime: now - 172800, // 2 days ago
      tags: [
        buildPipelineTag({key: DagsterTag.Backfill, value: 'abc123'}),
        buildPipelineTag({key: DagsterTag.User, value: 'bob@company.com'}),
      ],
    }),
    buildRun({
      runStatus: RunStatus.SUCCESS,
      id: 'automation-1',
      jobName: '__ASSET_JOB',
      creationTime: now - 1209600, // 2 weeks ago
      tags: [
        buildPipelineTag({key: DagsterTag.Automaterialize, value: 'true'}),
        buildPipelineTag({key: DagsterTag.AutomationCondition, value: 'true'}),
      ],
    }),
  ];

  return (
    <StorybookProvider>
      <RunRowWrapper>
        {runs.map((entry) => (
          <RunsFeedRow key={entry.id} entry={entry} />
        ))}
      </RunRowWrapper>
    </StorybookProvider>
  );
};

// Time formatting examples
export const TimeRangeExamples = () => {
  const now = Date.now() / 1000;
  const runs = [
    buildRun({
      runStatus: RunStatus.SUCCESS,
      id: 'recent-1',
      jobName: 'recent_job',
      creationTime: now - 17, // 17 seconds ago
      tags: [buildPipelineTag({key: DagsterTag.User, value: 'user@example.com'})],
    }),
    buildRun({
      runStatus: RunStatus.SUCCESS,
      id: 'recent-2',
      jobName: 'recent_job',
      creationTime: now - 300, // 5 minutes ago
      tags: [buildPipelineTag({key: DagsterTag.User, value: 'user@example.com'})],
    }),
    buildRun({
      runStatus: RunStatus.SUCCESS,
      id: 'recent-3',
      jobName: 'recent_job',
      creationTime: now - 7200, // 2 hours ago
      tags: [buildPipelineTag({key: DagsterTag.User, value: 'user@example.com'})],
    }),
    buildRun({
      runStatus: RunStatus.SUCCESS,
      id: 'recent-4',
      jobName: 'recent_job',
      creationTime: now - 172800, // 2 days ago
      tags: [buildPipelineTag({key: DagsterTag.User, value: 'user@example.com'})],
    }),
    buildRun({
      runStatus: RunStatus.SUCCESS,
      id: 'recent-5',
      jobName: 'recent_job',
      creationTime: now - 1209600, // 2 weeks ago
      tags: [buildPipelineTag({key: DagsterTag.User, value: 'user@example.com'})],
    }),
  ];

  return (
    <StorybookProvider>
      <RunRowWrapper>
        {runs.map((entry) => (
          <RunsFeedRow key={entry.id} entry={entry} />
        ))}
      </RunRowWrapper>
    </StorybookProvider>
  );
};
