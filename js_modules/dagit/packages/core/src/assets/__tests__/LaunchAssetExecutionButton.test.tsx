/* eslint-disable jest/expect-expect */
import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import React from 'react';

import {CustomAlertProvider} from '../../app/CustomAlertProvider';
import {LaunchPartitionBackfillMutation} from '../../instance/types/BackfillUtils.types';
import {LaunchPipelineExecutionMutation} from '../../runs/types/RunUtils.types';
import {TestProvider} from '../../testing/TestProvider';
import {
  AssetsInScope,
  ERROR_INVALID_ASSET_SELECTION,
  LaunchAssetExecutionButton,
} from '../LaunchAssetExecutionButton';
import {
  ASSET_DAILY,
  ASSET_DAILY_PARTITION_KEYS,
  ASSET_WEEKLY,
  ASSET_WEEKLY_ROOT,
  buildConfigPartitionSelectionLatestPartitionMock,
  buildExpectedLaunchBackfillMutation,
  buildExpectedLaunchSingleRunMutation,
  buildLaunchAssetLoaderMock,
  LaunchAssetCheckUpstreamWeeklyRootMock,
  LaunchAssetChoosePartitionsMock,
  LaunchAssetLoaderResourceJob7Mock,
  LaunchAssetLoaderResourceJob8Mock,
  LaunchAssetLoaderResourceMyAssetJobMock,
  PartitionHealthAssetMocks,
  UNPARTITIONED_ASSET,
  UNPARTITIONED_ASSET_OTHER_REPO,
  UNPARTITIONED_ASSET_WITH_REQUIRED_CONFIG,
} from '../__fixtures__/LaunchAssetExecutionButton.fixtures';

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../graph/asyncGraphLayout', () => ({}));

describe('LaunchAssetExecutionButton', () => {
  describe('labeling', () => {
    it('should say "Materialize all" for an `all` scope', async () => {
      await renderButton({scope: {all: [UNPARTITIONED_ASSET, UNPARTITIONED_ASSET_OTHER_REPO]}});
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual(
        'Materialize all',
      );
    });

    it('should say "Materialize all…" for an `all` scope if assets are partitioned', async () => {
      await renderButton({scope: {all: [UNPARTITIONED_ASSET, ASSET_DAILY]}});
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual(
        'Materialize all…',
      );
    });

    it('should say "Materialize" for an `all` scope if skipAllTerm is passed', async () => {
      await renderButton({scope: {all: [UNPARTITIONED_ASSET], skipAllTerm: true}});
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual('Materialize');
    });

    it('should say "Materialize…" for an `all` scope if assets are partitioned and skipAllTerm is passed', async () => {
      await renderButton({scope: {all: [UNPARTITIONED_ASSET, ASSET_DAILY], skipAllTerm: true}});
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual('Materialize…');
    });

    it('should say "Materialize selected" for an `selected` scope', async () => {
      await renderButton({scope: {selected: [UNPARTITIONED_ASSET]}});
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual(
        'Materialize selected',
      );
    });

    it('should say "Materialize selected…" for an `selected` scope with a partitioned asset', async () => {
      await renderButton({scope: {selected: [ASSET_DAILY]}});
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual(
        'Materialize selected…',
      );
    });

    it('should say "Materialize selected (2)…" for an `selected` scope with two items', async () => {
      await renderButton({scope: {selected: [UNPARTITIONED_ASSET, ASSET_DAILY]}});
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual(
        'Materialize selected (2)…',
      );
    });
  });

  describe('unpartitioned assets', () => {
    it('should directly launch via the in-context asset job', async () => {
      const launchMock = buildExpectedLaunchSingleRunMutation({
        mode: 'default',
        executionMetadata: {
          tags: [],
        },
        runConfigData: '{}',
        selector: {
          repositoryLocationName: 'test.py',
          repositoryName: 'repo',
          pipelineName: 'my_asset_job',
          assetSelection: [{path: ['unpartitioned_asset']}],
        },
      });
      await renderButton({
        scope: {all: [UNPARTITIONED_ASSET]},
        preferredJobName: 'my_asset_job',
        launchMock,
      });
      await clickMaterializeButton();
      await waitFor(() => expect(launchMock.result).toHaveBeenCalled());
    });

    it('should directly launch via the hidden job if no job is in context', async () => {
      const launchMock = buildExpectedLaunchSingleRunMutation({
        mode: 'default',
        executionMetadata: {
          tags: [],
        },
        runConfigData: '{}',
        selector: {
          repositoryLocationName: 'test.py',
          repositoryName: 'repo',
          pipelineName: '__ASSET_JOB_7',
          assetSelection: [{path: ['unpartitioned_asset']}],
        },
      });
      await renderButton({
        scope: {all: [UNPARTITIONED_ASSET]},
        preferredJobName: undefined,
        launchMock,
      });
      await clickMaterializeButton();
      await waitFor(() => expect(launchMock.result).toHaveBeenCalled());
    });

    it('should show the launchpad if an asset or resource requires config', async () => {
      await renderButton({
        scope: {all: [UNPARTITIONED_ASSET_WITH_REQUIRED_CONFIG]},
        preferredJobName: undefined,
      });
      await clickMaterializeButton();
      await waitFor(() => expect(screen.getByText('Launchpad (configure assets)')).toBeVisible());
    });

    it('should show an error if the assets do not share a code location', async () => {
      await renderButton({
        scope: {all: [UNPARTITIONED_ASSET, UNPARTITIONED_ASSET_OTHER_REPO]},
        preferredJobName: undefined,
      });
      await clickMaterializeButton();
      await expectErrorShown(ERROR_INVALID_ASSET_SELECTION);
    });
  });

  describe('partitioned assets', () => {
    it('should show the partition dialog', async () => {
      await renderButton({scope: {all: [ASSET_DAILY]}});
      await clickMaterializeButton();
      await waitFor(() => screen.findByTestId('choose-partitions-dialog'));
    });

    it('should launch single runs using the job in context if specified', async () => {
      const launchMock = buildExpectedLaunchSingleRunMutation({
        executionMetadata: {
          tags: [
            {key: 'dagster/partition', value: '2023-02-22'},
            {key: 'dagster/partition_set', value: 'my_asset_job_partition_set'},
          ],
        },
        mode: 'default',
        runConfigData: '{}\n',
        selector: {
          assetSelection: [{path: ['asset_daily']}],
          pipelineName: 'my_asset_job',
          repositoryLocationName: 'test.py',
          repositoryName: 'repo',
        },
      });
      await renderButton({
        scope: {all: [ASSET_DAILY]},
        preferredJobName: 'my_asset_job',
        launchMock,
      });
      await clickMaterializeButton();
      await waitFor(() => screen.findByTestId('choose-partitions-dialog'));
      await (await screen.findByTestId('latest-partition-button')).click();

      await expectLaunchExecutesMutationAndCloses('Launch 1 run', launchMock);
    });

    it('should launch backfills using the job in context if specified', async () => {
      const launchMock = buildExpectedLaunchBackfillMutation({
        selector: {
          partitionSetName: 'my_asset_job_partition_set',
          repositorySelector: {repositoryLocationName: 'test.py', repositoryName: 'repo'},
        },
        assetSelection: [{path: ['asset_daily']}],
        partitionNames: ASSET_DAILY_PARTITION_KEYS,
        fromFailure: false,
        tags: [],
      });
      await renderButton({
        scope: {all: [ASSET_DAILY]},
        preferredJobName: 'my_asset_job',
        launchMock,
      });
      await clickMaterializeButton();
      await waitFor(() => screen.findByTestId('choose-partitions-dialog'));

      const launchButton = await screen.findByTestId('launch-button');

      // verify that the missing only checkbox updates the number of runs
      expect(launchButton.textContent).toEqual('Launch 1148-run backfill');
      await (await screen.getByTestId('missing-only-checkbox')).click();
      expect(launchButton.textContent).toEqual('Launch 1046-run backfill');
      await (await screen.getByTestId('missing-only-checkbox')).click();

      // verify that the executed mutation is correct
      await expectLaunchExecutesMutationAndCloses('Launch 1148-run backfill', launchMock);
    });

    it('should launch single runs via the hidden job if no job is in context', async () => {
      const launchMock = buildExpectedLaunchSingleRunMutation({
        executionMetadata: {
          tags: [
            {key: 'dagster/partition', value: '2023-02-22'},
            {key: 'dagster/partition_set', value: '__ASSET_JOB_7_partition_set'},
          ],
        },
        mode: 'default',
        runConfigData: '{}\n',
        selector: {
          assetSelection: [{path: ['asset_daily']}],
          pipelineName: '__ASSET_JOB_7',
          repositoryLocationName: 'test.py',
          repositoryName: 'repo',
        },
      });
      await renderButton({
        scope: {all: [ASSET_DAILY]},
        preferredJobName: undefined,
        launchMock,
      });
      await clickMaterializeButton();
      await waitFor(() => screen.findByTestId('choose-partitions-dialog'));
      await (await screen.findByTestId('latest-partition-button')).click();
      await expectLaunchExecutesMutationAndCloses('Launch 1 run', launchMock);
    });

    it('should launch backfills as pure-asset backfills if no job is in context', async () => {
      const launchMock = buildExpectedLaunchBackfillMutation({
        selector: undefined,
        assetSelection: [{path: ['asset_daily']}],
        partitionNames: ASSET_DAILY_PARTITION_KEYS,
        fromFailure: false,
        tags: [],
      });
      await renderButton({
        scope: {all: [ASSET_DAILY]},
        preferredJobName: undefined,
        launchMock,
      });
      await clickMaterializeButton();
      await waitFor(() => screen.findByTestId('choose-partitions-dialog'));

      // missing-and-failed only option is available
      expect(await screen.getByTestId('missing-only-checkbox')).toBeEnabled();

      // ranges-as-tags option is available
      const rangesAsTags = await screen.getByTestId('ranges-as-tags-true-radio');
      await waitFor(async () => expect(rangesAsTags).toBeEnabled());

      await expectLaunchExecutesMutationAndCloses('Launch 1148-run backfill', launchMock);
    });

    it('should launch a single run if you choose to pass the partition range using tags', async () => {
      const launchMock = buildExpectedLaunchSingleRunMutation({
        mode: 'default',
        executionMetadata: {
          tags: [
            {key: 'dagster/asset_partition_range_start', value: '2020-01-02'},
            {key: 'dagster/asset_partition_range_end', value: '2023-02-22'},
          ],
        },
        runConfigData: '{}\n',
        selector: {
          repositoryLocationName: 'test.py',
          repositoryName: 'repo',
          pipelineName: 'my_asset_job',
          assetSelection: [{path: ['asset_daily']}],
        },
      });
      await renderButton({
        scope: {all: [ASSET_DAILY]},
        preferredJobName: 'my_asset_job',
        launchMock,
      });
      await clickMaterializeButton();
      await waitFor(() => screen.findByTestId('choose-partitions-dialog'));

      const rangesAsTags = await screen.getByTestId('ranges-as-tags-true-radio');
      await waitFor(async () => expect(rangesAsTags).toBeEnabled());
      await rangesAsTags.click();
      await expectLaunchExecutesMutationAndCloses('Launch 1 run', launchMock);
    });
  });

  describe('partition mapped assets', () => {
    it('should show the partition dialog with an anchor asset', async () => {
      const LaunchMutationMock = buildExpectedLaunchBackfillMutation({
        selector: undefined,
        assetSelection: [{path: ['asset_daily']}, {path: ['asset_weekly']}],
        partitionNames: ASSET_DAILY_PARTITION_KEYS,
        fromFailure: false,
        tags: [],
      });

      await renderButton({
        scope: {all: [ASSET_DAILY, ASSET_WEEKLY]},
        launchMock: LaunchMutationMock,
      });

      await clickMaterializeButton();

      // expect the dialog to be displayed
      await waitFor(() => screen.findByTestId('choose-partitions-dialog'));

      // expect the anchor asset to be labeled
      expect(await screen.getByTestId('anchor-asset-label')).toHaveTextContent('asset_daily');

      // backfill options for run as tags, missing only are not available
      expect(await screen.queryByTestId('missing-only-checkbox')).toBeNull();
      expect(await screen.queryByTestId('ranges-as-tags-true-radio')).toBeNull();

      await expectLaunchExecutesMutationAndCloses('Launch backfill', LaunchMutationMock);
    });

    it('should show an error if two roots have different partition defintions', async () => {
      await renderButton({
        scope: {all: [ASSET_DAILY, ASSET_WEEKLY, ASSET_WEEKLY_ROOT]},
      });
      await clickMaterializeButton();
      await expectErrorShown(ERROR_INVALID_ASSET_SELECTION);
    });
  });
});

// Helpers to make tests more concise

async function renderButton({
  scope,
  launchMock,
  preferredJobName,
}: {
  scope: AssetsInScope;
  launchMock?: MockedResponse<Record<string, any>>;
  preferredJobName?: string;
}) {
  const assetKeys = ('all' in scope ? scope.all : scope.selected).map((s) => s.assetKey);

  const mocks: MockedResponse<Record<string, any>>[] = [
    LaunchAssetChoosePartitionsMock,
    LaunchAssetLoaderResourceJob7Mock,
    LaunchAssetLoaderResourceJob8Mock,
    LaunchAssetLoaderResourceMyAssetJobMock,
    LaunchAssetCheckUpstreamWeeklyRootMock,
    ...PartitionHealthAssetMocks,
    buildConfigPartitionSelectionLatestPartitionMock('2020-01-02', 'my_asset_job_partition_set'),
    buildConfigPartitionSelectionLatestPartitionMock('2023-02-22', 'my_asset_job_partition_set'),
    buildConfigPartitionSelectionLatestPartitionMock('2023-02-22', '__ASSET_JOB_7_partition_set'),
    buildLaunchAssetLoaderMock(assetKeys),
    ...(launchMock ? [launchMock] : []),
  ];

  await act(async () => {
    render(
      <TestProvider>
        <CustomAlertProvider />
        <MockedProvider mocks={mocks}>
          <LaunchAssetExecutionButton scope={scope} preferredJobName={preferredJobName} />
        </MockedProvider>
      </TestProvider>,
    );
  });
}

async function clickMaterializeButton() {
  const materializeButton = await screen.findByTestId('materialize-button');
  expect(materializeButton).toBeVisible();
  materializeButton.click();
}

async function expectErrorShown(msg: string) {
  // expect an error to be displayed
  await waitFor(async () => {
    await screen.findByTestId('alert-body');
  });
  expect(await screen.findByTestId('alert-body')).toHaveTextContent(msg);
}

async function expectLaunchExecutesMutationAndCloses(
  label: string,
  mutation:
    | MockedResponse<LaunchPartitionBackfillMutation>
    | MockedResponse<LaunchPipelineExecutionMutation>,
) {
  const launchButton = await screen.findByTestId('launch-button');
  expect(launchButton.textContent).toEqual(label);
  await launchButton.click();

  // expect that it triggers the mutation (variables checked by mock matching)
  await waitFor(() => expect(mutation.result).toHaveBeenCalled());

  // expect the dialog to close
  await waitFor(async () => {
    expect(await screen.queryByTestId('choose-partitions-dialog')).toBeNull();
  });
}
