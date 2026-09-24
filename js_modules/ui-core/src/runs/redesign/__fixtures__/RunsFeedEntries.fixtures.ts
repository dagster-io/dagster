import {
  buildAssetCheckhandle,
  buildAssetKey,
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

export const buildRunSummary = (
  overrides: Partial<RunSummaryFragment> = {},
): RunSummaryFragment => ({
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

export const buildBackfillSummary = (
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

// Statuses

export const notStartedRun = runEntry({
  id: 'not-started-run-id',
  runStatus: RunStatus.NOT_STARTED,
  startTime: null,
  endTime: null,
});

export const queuedRun = runEntry({
  id: 'queued-run-id',
  runStatus: RunStatus.QUEUED,
  startTime: null,
  endTime: null,
});

export const startingRun = runEntry({
  id: 'starting-run-id',
  runStatus: RunStatus.STARTING,
  startTime: null,
  endTime: null,
});

export const startedRun = runEntry({
  id: 'started-run-id',
  runStatus: RunStatus.STARTED,
  startTime: LIVE_STARTED_AT,
  endTime: null,
});

export const startedRunWithoutStartTime = runEntry({
  id: 'started-no-start-run-id',
  runStatus: RunStatus.STARTED,
  startTime: null,
  endTime: null,
});

export const managedRun = runEntry({
  id: 'managed-run-id',
  runStatus: RunStatus.MANAGED,
  startTime: LIVE_STARTED_AT,
  endTime: null,
});

export const cancelingRun = runEntry({
  id: 'canceling-run-id',
  runStatus: RunStatus.CANCELING,
  startTime: LIVE_STARTED_AT,
  endTime: null,
});

export const succeededRun = runEntry({id: 'succeeded-run-id'});

export const failedRun = runEntry({id: 'failed-run-id', runStatus: RunStatus.FAILURE});

export const failedWillRetryRun = runEntry({
  id: 'failed-retry-run-id',
  runStatus: RunStatus.FAILURE,
  tags: [tag('dagster/will_retry', 'true')],
});

export const canceledRun = runEntry({id: 'canceled-run-id', runStatus: RunStatus.CANCELED});

/** A failed launch is reported with its end time as its start time. */
export const failedToStartRun = runEntry({
  id: 'failed-to-start-run-id',
  runStatus: RunStatus.FAILURE,
  startTime: ENDED_AT,
  endTime: ENDED_AT,
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

// Selections

const salesDaily = buildAssetKey({path: ['sales', 'daily']});
const slashAsset = buildAssetKey({path: ['a/b']});
const nestedAsset = buildAssetKey({path: ['a', 'b']});

const manyAssets = Array.from({length: 25}, (_, index) =>
  buildAssetKey({path: ['warehouse', `table_${index}`]}),
);

export const completeSelectionRun = runEntry({
  id: 'complete-selection-run-id',
  jobName: REAL_JOB_NAME,
  assetSelectionPreview: [salesDaily, slashAsset, nestedAsset],
  assetSelectionCount: 3,
});

export const incompleteSelectionRun = runEntry({
  id: 'incomplete-selection-run-id',
  assetSelectionPreview: manyAssets,
  assetSelectionCount: 40,
});

export const unknownSelectionsRun = runEntry({
  id: 'unknown-selection-run-id',
  jobName: REAL_JOB_NAME,
  assetSelectionPreview: null,
  assetCheckSelectionPreview: null,
});

export const emptyWholeJobRun = runEntry({id: 'whole-job-run-id', jobName: REAL_JOB_NAME});

export const emptyHiddenAssetJobRun = runEntry({id: 'empty-hidden-job-run-id'});

export const checksOnlyRun = runEntry({
  id: 'checks-only-run-id',
  jobName: REAL_JOB_NAME,
  assetCheckSelectionPreview: [
    buildAssetCheckhandle({assetKey: salesDaily, name: 'freshness'}),
    buildAssetCheckhandle({assetKey: salesDaily, name: 'row_count'}),
  ],
  assetCheckSelectionCount: 2,
});

export const assetsKnownChecksUnknownRun = runEntry({
  id: 'assets-known-checks-unknown-run-id',
  assetSelectionPreview: [salesDaily],
  assetSelectionCount: 1,
  assetCheckSelectionPreview: null,
});

export const checksKnownAssetsUnknownRun = runEntry({
  id: 'checks-known-assets-unknown-run-id',
  assetSelectionPreview: null,
  assetCheckSelectionPreview: [buildAssetCheckhandle({assetKey: salesDaily, name: 'freshness'})],
  assetCheckSelectionCount: 1,
});

export const singlePartitionRun = runEntry({
  id: 'single-partition-run-id',
  assetSelectionPreview: [salesDaily],
  assetSelectionCount: 1,
  tags: [tag(DagsterTag.Partition, '2026-09-08')],
});

export const partitionRangeRun = runEntry({
  id: 'partition-range-run-id',
  assetSelectionPreview: [salesDaily],
  assetSelectionCount: 1,
  tags: [
    tag(DagsterTag.AssetPartitionRangeStart, '2026-09-01'),
    tag(DagsterTag.AssetPartitionRangeEnd, '2026-09-08'),
  ],
});
