import {
  buildAssetCheckhandle,
  buildAssetKey,
  buildExecutionPlan,
  buildExecutionStep,
  buildPartitionBackfill,
  buildPipelineTag,
  buildRun,
} from '../../../graphql/builders';
import {BulkActionStatus, RunStatus} from '../../../graphql/types';
import {mapRunSelectionDetails, mapRunsFeedEntry} from '../mapRunsFeedData';
import {
  BackfillSummaryFragment,
  RunSelectionDetailsFragment,
  RunSummaryFragment,
} from '../types/RunsFeedFragments.types';

const buildRunSummary = (overrides: Partial<RunSummaryFragment> = {}): RunSummaryFragment => ({
  ...buildRun({
    runStatus: RunStatus.STARTED,
    creationTime: 0,
    startTime: null,
    endTime: null,
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
  ...buildPartitionBackfill(),
  backfillStatus: BulkActionStatus.REQUESTED,
  backfillJobName: null,
  ...overrides,
});

const buildRunSelectionDetails = (
  overrides: Partial<RunSelectionDetailsFragment> = {},
): RunSelectionDetailsFragment => ({...buildRun(), ...overrides});

const tag = (key: string, value: string) => buildPipelineTag({key, value});
const asset = buildAssetKey({path: ['asset']});

describe('mapRunsFeedEntry', () => {
  it.each([
    {preview: null, count: 0, expected: null},
    {preview: null, count: 4, expected: null},
    {preview: [], count: 0, expected: {preview: [], count: 0, complete: true}},
    {preview: [], count: 1, expected: null},
    {preview: [asset], count: 0, expected: null},
    {preview: [asset], count: -1, expected: null},
    {preview: [asset], count: 1, expected: {preview: [asset], count: 1, complete: true}},
    {preview: [asset], count: 2, expected: {preview: [asset], count: 2, complete: false}},
  ])('normalizes selection preview $preview with count $count', ({preview, count, expected}) => {
    const row = mapRunsFeedEntry(
      buildRunSummary({assetSelectionPreview: preview, assetSelectionCount: count}),
    );
    expect(row.selectionPreviews?.assets).toEqual(expected);
    expect(row.selectionPreviews?.checks).toEqual({preview: [], count: 0, complete: true});
  });

  it('keeps check knowledge independent and preserves structured target keys', () => {
    const flatAsset = buildAssetKey({path: ['a/b']});
    const assets = [flatAsset, buildAssetKey({path: ['a', 'b']})];
    const check = buildAssetCheckhandle({assetKey: flatAsset, name: 'freshness'});
    const run = buildRunSummary({assetSelectionPreview: assets, assetSelectionCount: 2});
    expect(mapRunsFeedEntry({...run, assetCheckSelectionPreview: null}).selectionPreviews).toEqual({
      assets: {preview: assets, count: 2, complete: true},
      checks: null,
    });
    expect(
      mapRunsFeedEntry({
        ...run,
        assetCheckSelectionPreview: [check],
        assetCheckSelectionCount: 2,
      }).selectionPreviews?.checks,
    ).toEqual({preview: [check], count: 2, complete: false});
    expect(
      mapRunsFeedEntry({...run, assetCheckSelectionPreview: [], assetCheckSelectionCount: 1})
        .selectionPreviews?.checks,
    ).toBeNull();
  });

  it('preserves recorded context and permissions for an automatic retry in a backfill', () => {
    const run = buildRunSummary({
      id: 'run-id',
      parentRunId: 'parent-id',
      rootRunId: 'root-id',
      hasReExecutePermission: false,
      hasDeletePermission: false,
      hasTerminatePermission: true,
      canTerminate: false,
      tags: [
        tag('dagster/retry_number', '2'),
        tag('dagster/backfill', 'backfill-id'),
        tag('dagster/sensor_name', 'files'),
        tag('dagster/from_automation_condition', 'true'),
        tag('dagster/asset_evaluation_id', 'evaluation-id'),
        tag('dagster/tick', 'tick-id'),
        tag('user', 'pat@example.com'),
        tag('dagster/partition', '2026-09-08|east'),
        tag('dagster/asset_partition_range_start', '2026-09-01'),
      ],
    });
    const row = mapRunsFeedEntry(run);
    expect(row).toMatchObject(run);
    expect(row).toMatchObject({isAutomaticRetry: true, href: '/runs/run-id'});
  });

  it.each([{tags: []}, {tags: [tag('dagster/backfill', 'backfill-id')]}])(
    'does not invent retry lineage from tags $tags',
    ({tags}) => {
      expect(mapRunsFeedEntry(buildRunSummary({tags}))).toMatchObject({
        tags,
        parentRunId: null,
        rootRunId: null,
        isAutomaticRetry: false,
      });
    },
  );

  it.each([undefined, '', 'false', 'FALSE', 'none', 'NoNe', '0'])(
    'decodes will_retry=%p as false',
    (value) => {
      const tags = value === undefined ? [] : [tag('dagster/will_retry', value)];
      expect(mapRunsFeedEntry(buildRunSummary({runStatus: RunStatus.FAILURE, tags}))).toMatchObject(
        {
          willRetry: false,
        },
      );
    },
  );

  it.each(['true', 'TRUE', 'yes', '1', ' false '])('decodes will_retry=%p as true', (value) => {
    expect(
      mapRunsFeedEntry(
        buildRunSummary({runStatus: RunStatus.FAILURE, tags: [tag('dagster/will_retry', value)]}),
      ),
    ).toMatchObject({willRetry: true, isAutomaticRetry: false});
  });

  it.each(Object.values(RunStatus))(
    'preserves %s and only marks failures for retry',
    (runStatus) => {
      expect(
        mapRunsFeedEntry(buildRunSummary({runStatus, tags: [tag('dagster/will_retry', 'true')]})),
      ).toMatchObject({runStatus, willRetry: runStatus === RunStatus.FAILURE});
    },
  );

  it.each(['', 'successor-id'])(
    'suppresses will-retry when a successor tag is present: %p',
    (value) => {
      expect(
        mapRunsFeedEntry(
          buildRunSummary({
            runStatus: RunStatus.FAILURE,
            tags: [tag('dagster/will_retry', 'true'), tag('dagster/auto_retry_run_id', value)],
          }),
        ),
      ).toMatchObject({willRetry: false});
    },
  );

  it.each([
    {
      name: 'running from epoch',
      runStatus: RunStatus.STARTED,
      startTime: 0,
      endTime: null,
      startAtMs: 0,
      durationMs: null,
    },
    {
      name: 'successful run with missing-start-time fallback',
      runStatus: RunStatus.SUCCESS,
      startTime: 20,
      endTime: 20,
      startAtMs: null,
      durationMs: null,
    },
    {
      name: 'failed run with missing-start-time fallback',
      runStatus: RunStatus.FAILURE,
      startTime: 20,
      endTime: 20,
      startAtMs: null,
      durationMs: null,
    },
    {
      name: 'canceled run with missing-start-time fallback',
      runStatus: RunStatus.CANCELED,
      startTime: 20,
      endTime: 20,
      startAtMs: null,
      durationMs: null,
    },
    {
      name: 'missing start time',
      runStatus: RunStatus.SUCCESS,
      startTime: null,
      endTime: 20,
      startAtMs: null,
      durationMs: null,
    },
    {
      name: 'missing start and end times',
      runStatus: RunStatus.FAILURE,
      startTime: null,
      endTime: null,
      startAtMs: null,
      durationMs: null,
    },
    {
      name: 'fractional seconds',
      runStatus: RunStatus.SUCCESS,
      startTime: 12.5,
      endTime: 14,
      startAtMs: 12500,
      durationMs: 1500,
    },
    {
      name: 'negative duration clamped to zero',
      runStatus: RunStatus.SUCCESS,
      startTime: 20,
      endTime: 15,
      startAtMs: 20000,
      durationMs: 0,
    },
    {
      name: 'running with equal start and end times',
      runStatus: RunStatus.STARTED,
      startTime: 20,
      endTime: 20,
      startAtMs: 20000,
      durationMs: 0,
    },
  ])(
    'normalizes $name while preserving recorded values',
    ({runStatus, startTime, endTime, startAtMs, durationMs}) => {
      expect(mapRunsFeedEntry(buildRunSummary({runStatus, startTime, endTime}))).toMatchObject({
        startTime,
        endTime,
        timing: {
          createdAtMs: 0,
          startAtMs,
          endAtMs: endTime === null ? null : endTime * 1000,
          durationMs,
        },
      });
    },
  );

  it.each([
    [BulkActionStatus.COMPLETED, RunStatus.SUCCESS],
    [BulkActionStatus.FAILING, RunStatus.FAILURE],
  ])(
    'preserves backfill status %s separately from its projection %s',
    (backfillStatus, runStatus) => {
      const backfill = buildBackfillSummary({
        id: 'backfill-id',
        backfillStatus,
        runStatus,
        startTime: 20,
        endTime: 20,
        hasCancelPermission: false,
        hasResumePermission: true,
      });
      expect(mapRunsFeedEntry(backfill)).toMatchObject({
        ...backfill,
        href: '/runs/b/backfill-id',
        selectionPreviews: null,
        timing: {startAtMs: 20000, endAtMs: 20000, durationMs: 0},
      });
    },
  );
});

describe('mapRunSelectionDetails', () => {
  it('annotates each check with whether its asset is also selected', () => {
    const selectedAsset = buildAssetKey({path: ['a/b']});
    const checkWithSelectedAsset = buildAssetCheckhandle({
      assetKey: selectedAsset,
      name: 'freshness',
    });
    const checkWithUnselectedAsset = buildAssetCheckhandle({
      assetKey: buildAssetKey({path: ['a', 'b']}),
      name: 'freshness',
    });
    const executionPlan = buildExecutionPlan({
      assetKeys: [buildAssetKey({path: ['attempt_only']})],
      steps: [buildExecutionStep({key: 'step_one'})],
    });
    const details = mapRunSelectionDetails(
      buildRunSelectionDetails({
        assetSelection: [selectedAsset],
        assetCheckSelection: [checkWithSelectedAsset, checkWithUnselectedAsset],
        executionPlan,
      }),
    );
    expect(details.assetSelection).toEqual([selectedAsset]);
    expect(details.annotatedChecks).toEqual([
      {...checkWithSelectedAsset, assetIsSelected: true},
      {...checkWithUnselectedAsset, assetIsSelected: false},
    ]);
    expect(details.executionPlan).toBe(executionPlan);
  });

  it.each([
    {assets: null, assetIsSelected: null},
    {assets: [], assetIsSelected: false},
  ])(
    'classifies check-only requests with assets=$assets as assetIsSelected=$assetIsSelected',
    ({assets, assetIsSelected}) => {
      const check = buildAssetCheckhandle({assetKey: asset, name: 'freshness'});
      expect(
        mapRunSelectionDetails(
          buildRunSelectionDetails({assetSelection: assets, assetCheckSelection: [check]}),
        ).annotatedChecks,
      ).toEqual([{...check, assetIsSelected}]);
    },
  );

  it.each([{selection: null}, {selection: []}])(
    'preserves unknown versus empty selections: $selection',
    ({selection}) => {
      expect(
        mapRunSelectionDetails(
          buildRunSelectionDetails({
            assetSelection: selection,
            assetCheckSelection: selection,
            executionPlan: null,
          }),
        ),
      ).toMatchObject({
        assetSelection: selection,
        annotatedChecks: selection,
        executionPlan: null,
      });
    },
  );
});
