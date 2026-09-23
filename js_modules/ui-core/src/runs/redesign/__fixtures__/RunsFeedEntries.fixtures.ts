import {
  buildPartitionBackfill,
  buildPipelineTag,
  buildRepositoryOrigin,
  buildRun,
} from '../../../graphql/builders';
import {BulkActionStatus, RunStatus} from '../../../graphql/types';
import {DagsterTag} from '../../RunTag';
import {mapRunsFeedEntry} from '../mapRunsFeedData';
import {BackfillSummaryFragment, RunSummaryFragment} from '../types/RunsFeedFragments.types';

/** Fixed clock the fixtures are written against; tests pin `Date.now()` to it. */
const FIXTURE_NOW_SECONDS = 1_757_000_000;
export const FIXTURE_NOW_MS = FIXTURE_NOW_SECONDS * 1000;

const CREATED_AT = FIXTURE_NOW_SECONDS - 600;
const STARTED_AT = FIXTURE_NOW_SECONDS - 540;
const ENDED_AT = FIXTURE_NOW_SECONDS - 300;
const LIVE_STARTED_AT = FIXTURE_NOW_SECONDS - 10;

const HIDDEN_ASSET_JOB_NAME = '__ASSET_JOB_0';
const REAL_JOB_NAME = 'daily_etl';

export const tag = (key: string, value: string) => buildPipelineTag({key, value});

const repositoryOrigin = buildRepositoryOrigin({
  id: 'origin-id',
  repositoryName: 'my_repo',
  repositoryLocationName: 'my_location',
});

const buildRunSummary = (overrides: Partial<RunSummaryFragment> = {}): RunSummaryFragment => ({
  ...buildRun({
    id: 'a1b2c3d4-1111-2222-3333-444455556666',
    runId: 'a1b2c3d4-1111-2222-3333-444455556666',
    runStatus: RunStatus.SUCCESS,
    creationTime: CREATED_AT,
    startTime: STARTED_AT,
    endTime: ENDED_AT,
    jobName: HIDDEN_ASSET_JOB_NAME,
    repositoryOrigin,
    tags: [],
    parentRunId: null,
    rootRunId: null,
    assetSelectionCount: 0,
    assetCheckSelectionCount: 0,
  }),
  assetSelectionPreview: [],
  assetCheckSelectionPreview: [],
  ...overrides,
});

const buildBackfillSummary = (
  overrides: Partial<BackfillSummaryFragment> = {},
): BackfillSummaryFragment => ({
  ...buildPartitionBackfill({
    id: 'backfill-id',
    runStatus: RunStatus.SUCCESS,
    creationTime: CREATED_AT,
    startTime: STARTED_AT,
    endTime: ENDED_AT,
    partitionSetName: null,
    isAssetBackfill: false,
    title: null,
    user: null,
    tags: [],
  }),
  backfillStatus: BulkActionStatus.COMPLETED,
  backfillJobName: null,
  ...overrides,
});

export const runEntry = (overrides: Partial<RunSummaryFragment> = {}) =>
  mapRunsFeedEntry(buildRunSummary(overrides));

export const backfillEntry = (overrides: Partial<BackfillSummaryFragment> = {}) =>
  mapRunsFeedEntry(buildBackfillSummary(overrides));

// Initiators

export const manualRun = runEntry({id: 'manual-run-id'});

export const manualRunWithUser = runEntry({
  id: 'manual-user-run-id',
  tags: [tag(DagsterTag.User, 'pat@example.com')],
});

export const scheduleRun = runEntry({
  id: 'schedule-run-id',
  tags: [tag(DagsterTag.ScheduleName, 'hourly_schedule')],
});

export const scheduleRunWithoutRepo = runEntry({
  id: 'schedule-no-repo-run-id',
  repositoryOrigin: null,
  tags: [tag(DagsterTag.ScheduleName, 'hourly_schedule')],
});

export const scheduleRunWithTick = runEntry({
  id: 'schedule-tick-run-id',
  tags: [tag(DagsterTag.ScheduleName, 'hourly_schedule'), tag(DagsterTag.TickId, 'tick-id')],
});

export const scheduleRunWithTickNoRepo = runEntry({
  id: 'schedule-tick-no-repo-run-id',
  repositoryOrigin: null,
  tags: [tag(DagsterTag.ScheduleName, 'hourly_schedule'), tag(DagsterTag.TickId, 'tick-id')],
});

export const sensorRun = runEntry({
  id: 'sensor-run-id',
  tags: [tag(DagsterTag.SensorName, 'files_sensor')],
});

export const defaultAutomationSensorRun = runEntry({
  id: 'default-da-run-id',
  tags: [
    tag(DagsterTag.SensorName, 'default_automation_condition_sensor'),
    tag(DagsterTag.AutomationCondition, 'true'),
    tag(DagsterTag.TickId, 'tick-id'),
  ],
});

export const namedAutomationSensorRun = runEntry({
  id: 'named-da-run-id',
  tags: [
    tag(DagsterTag.SensorName, 'my_automation_sensor'),
    tag(DagsterTag.AutomationCondition, 'true'),
  ],
});

export const legacyAutomationConditionTickRun = runEntry({
  id: 'legacy-da-run-id',
  tags: [tag(DagsterTag.AutomationCondition, 'true'), tag(DagsterTag.TickId, 'tick-id')],
});

export const autoMaterializeRun = runEntry({
  id: 'auto-materialize-run-id',
  tags: [tag(DagsterTag.Automaterialize, 'true')],
});

export const createdByAutoMaterializeRun = runEntry({
  id: 'created-by-am-run-id',
  tags: [tag(DagsterTag.CreatedBy, 'auto_materialize')],
});

export const autoObserveRun = runEntry({
  id: 'auto-observe-run-id',
  tags: [tag(DagsterTag.AutoObserve, 'true')],
});

export const backfillChildRun = runEntry({
  id: 'backfill-child-run-id',
  tags: [tag(DagsterTag.Backfill, 'bkfl1234')],
});

export const reExecutionRun = runEntry({
  id: 'reexecution-run-id',
  parentRunId: 'pppppppp-1111-2222-3333-444455556666',
  rootRunId: 'pppppppp-1111-2222-3333-444455556666',
  tags: [tag(DagsterTag.User, 'pat@example.com')],
});

export const autoRetryInBackfillRun = runEntry({
  id: 'auto-retry-run-id',
  parentRunId: 'pppppppp-1111-2222-3333-444455556666',
  rootRunId: 'pppppppp-1111-2222-3333-444455556666',
  tags: [
    tag('dagster/retry_number', '1'),
    tag(DagsterTag.Backfill, 'bkfl1234'),
    tag(DagsterTag.User, 'pat@example.com'),
  ],
});

// Backfills

export const assetBackfill = backfillEntry({
  id: 'asset-backfill-id',
  isAssetBackfill: true,
  user: 'pat@example.com',
});

export const jobBackfill = backfillEntry({
  id: 'job-backfill-id',
  backfillJobName: REAL_JOB_NAME,
  partitionSetName: 'daily_etl_partition_set',
});

export const partitionSetBackfill = backfillEntry({
  id: 'partition-set-backfill-id',
  partitionSetName: 'daily_etl_partition_set',
});

export const inProgressBackfill = backfillEntry({
  id: 'in-progress-backfill-id',
  runStatus: RunStatus.STARTED,
  backfillStatus: BulkActionStatus.REQUESTED,
  isAssetBackfill: true,
  startTime: LIVE_STARTED_AT,
  endTime: null,
});
