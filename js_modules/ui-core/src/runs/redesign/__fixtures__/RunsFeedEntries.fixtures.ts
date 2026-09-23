import {
  buildPartitionBackfill,
  buildPipelineTag,
  buildRepositoryOrigin,
  buildRun,
} from '../../../graphql/builders';
import {BulkActionStatus, RunStatus} from '../../../graphql/types';
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
