/* eslint-disable jest/expect-expect */
import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

import {CustomAlertProvider} from '../../app/CustomAlertProvider';
import {LaunchPartitionBackfillMutation} from '../../instance/backfill/types/BackfillUtils.types';
import {LaunchPipelineExecutionMutation} from '../../runs/types/RunUtils.types';
import {TestProvider} from '../../testing/TestProvider';
import * as WorkspaceContext from '../../workspace/WorkspaceContext';
import {
  AssetsInScope,
  ERROR_INVALID_ASSET_SELECTION,
  LaunchAssetExecutionButton,
} from '../LaunchAssetExecutionButton';
import {
  ASSET_DAILY,
  ASSET_DAILY_PARTITION_KEYS,
  ASSET_DAILY_PARTITION_KEYS_MISSING,
  ASSET_WEEKLY,
  ASSET_WEEKLY_ROOT,
  LaunchAssetCheckUpstreamWeeklyRootMock,
  LaunchAssetLoaderResourceJob7Mock,
  LaunchAssetLoaderResourceJob8Mock,
  LaunchAssetLoaderResourceMyAssetJobMock,
  PartitionHealthAssetMocks,
  UNPARTITIONED_ASSET,
  UNPARTITIONED_ASSET_OTHER_REPO,
  UNPARTITIONED_ASSET_WITH_REQUIRED_CONFIG,
  UNPARTITIONED_NON_EXECUTABLE_ASSET,
  UNPARTITIONED_SOURCE_ASSET,
  buildConfigPartitionSelectionLatestPartitionMock,
  buildExpectedLaunchBackfillMutation,
  buildExpectedLaunchSingleRunMutation,
  buildLaunchAssetLoaderMock,
  buildLaunchAssetWarningsMock,
} from '../__fixtures__/LaunchAssetExecutionButton.fixtures';

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../graph/asyncGraphLayout', () => ({}));

const flagSpy = jest.spyOn(WorkspaceContext, 'useFeatureFlagForCodeLocation');

describe('LaunchAssetExecutionButton', () => {
  describe('labeling', () => {
    it('should say "Materialize all" for an `all` scope', async () => {
      renderButton({scope: {all: [UNPARTITIONED_ASSET, UNPARTITIONED_ASSET_OTHER_REPO]}});
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual(
        'Materialize all',
      );
    });

    it('should say "Materialize all…" for an `all` scope if assets are partitioned', async () => {
      renderButton({scope: {all: [UNPARTITIONED_ASSET, ASSET_DAILY]}});
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual(
        'Materialize all…',
      );
    });

    it('should say "Materialize" for an `all` scope if skipAllTerm is passed', async () => {
      renderButton({scope: {all: [UNPARTITIONED_ASSET], skipAllTerm: true}});
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual('Materialize');
    });

    it('should say "Materialize…" for an `all` scope if assets are partitioned and skipAllTerm is passed', async () => {
      renderButton({scope: {all: [UNPARTITIONED_ASSET, ASSET_DAILY], skipAllTerm: true}});
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual('Materialize…');
    });

    it('should say "Materialize selected" for an `selected` scope', async () => {
      renderButton({scope: {selected: [UNPARTITIONED_ASSET]}});
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual(
        'Materialize selected',
      );
    });

    it('should say "Materialize selected…" for an `selected` scope with a partitioned asset', async () => {
      renderButton({scope: {selected: [ASSET_DAILY]}});
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual(
        'Materialize selected…',
      );
    });

    it('should say "Materialize selected (2)…" for an `selected` scope with two items', async () => {
      renderButton({scope: {selected: [UNPARTITIONED_ASSET, ASSET_DAILY]}});
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual(
        'Materialize selected (2)…',
      );
    });
  });

  describe('source assets', () => {
    it('should skip over source assets in the selection', async () => {
      renderButton({
        scope: {selected: [UNPARTITIONED_ASSET, UNPARTITIONED_SOURCE_ASSET, ASSET_DAILY]},
      });
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual(
        'Materialize selected (2)…', // 2 instead of 3
      );
    });

    it('should be disabled if the entire selection is source assets', async () => {
      renderButton({
        scope: {selected: [UNPARTITIONED_SOURCE_ASSET]},
      });
      const button = await screen.findByTestId('materialize-button');
      expect(button).toBeDisabled();

      userEvent.hover(button);
      expect(await screen.findByText('Source assets cannot be materialized')).toBeDefined();
    });
  });

  describe('non-executable assets', () => {
    it('should skip over non-executable assets in the selection', async () => {
      renderButton({
        scope: {selected: [UNPARTITIONED_ASSET, UNPARTITIONED_NON_EXECUTABLE_ASSET, ASSET_DAILY]},
      });
      expect((await screen.findByTestId('materialize-button')).textContent).toEqual(
        'Materialize selected (2)…', // 2 instead of 3
      );
    });

    it('should be disabled if the entire selection is non-executable assets', async () => {
      renderButton({
        scope: {selected: [UNPARTITIONED_NON_EXECUTABLE_ASSET]},
      });
      const button = await screen.findByTestId('materialize-button');
      expect(button).toBeDisabled();

      userEvent.hover(button);
      expect(await screen.findByText('External assets cannot be materialized')).toBeDefined();
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
          assetCheckSelection: [],
        },
      });
      renderButton({
        scope: {all: [UNPARTITIONED_ASSET]},
        preferredJobName: 'my_asset_job',
        launchMock,
      });
      await clickMaterializeButton();
      await waitFor(() => expect(launchMock.result).toHaveBeenCalled());
    });

    describe('permissions', () => {
      it('should be disabled if you do not have permission to execute assets', async () => {
        renderButton({
          scope: {all: [{...UNPARTITIONED_ASSET, hasMaterializePermission: false}]},
        });
        const button = await screen.findByTestId('materialize-button');
        expect(button).toBeDisabled();

        userEvent.hover(button);
        expect(
          await screen.findByText('You do not have permission to materialize assets'),
        ).toBeDefined();
      });
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
          assetCheckSelection: [],
        },
      });
      renderButton({
        scope: {all: [UNPARTITIONED_ASSET]},
        preferredJobName: undefined,
        launchMock,
      });
      await clickMaterializeButton();
      await waitFor(() => expect(launchMock.result).toHaveBeenCalled());
    });

    it('should show the launchpad if an asset or resource requires config', async () => {
      renderButton({
        scope: {all: [UNPARTITIONED_ASSET_WITH_REQUIRED_CONFIG]},
        preferredJobName: undefined,
      });
      await clickMaterializeButton();
      await waitFor(() => expect(screen.getByText('Launchpad (configure assets)')).toBeVisible());
    });

    it('should show an error if the assets do not share a code location', async () => {
      renderButton({
        scope: {all: [UNPARTITIONED_ASSET, UNPARTITIONED_ASSET_OTHER_REPO]},
        preferredJobName: undefined,
      });
      await clickMaterializeButton();
      await expectErrorShown(ERROR_INVALID_ASSET_SELECTION);
    });
  });

  describe('partitioned assets', () => {
    it('should show the partition dialog', async () => {
      renderButton({scope: {all: [ASSET_DAILY]}});
      await clickMaterializeButton();
      await screen.findByTestId('choose-partitions-dialog');
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
          assetCheckSelection: [],
          pipelineName: 'my_asset_job',
          repositoryLocationName: 'test.py',
          repositoryName: 'repo',
        },
      });
      renderButton({
        scope: {all: [ASSET_DAILY]},
        preferredJobName: 'my_asset_job',
        launchMock,
      });
      await clickMaterializeButton();
      await screen.findByTestId('choose-partitions-dialog');
      await userEvent.click(await screen.findByTestId('latest-partition-button'));

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
      renderButton({
        scope: {all: [ASSET_DAILY]},
        preferredJobName: 'my_asset_job',
        launchMock,
      });
      await clickMaterializeButton();
      await screen.findByTestId('choose-partitions-dialog');

      // verify that the executed mutation is correct
      await expectLaunchExecutesMutationAndCloses('Launch backfill', launchMock);
    });

    it('should launch backfills with only missing partitions if requested', async () => {
      const launchMock = buildExpectedLaunchBackfillMutation({
        selector: {
          partitionSetName: 'my_asset_job_partition_set',
          repositorySelector: {repositoryLocationName: 'test.py', repositoryName: 'repo'},
        },
        assetSelection: [{path: ['asset_daily']}],
        partitionNames: ASSET_DAILY_PARTITION_KEYS_MISSING,
        fromFailure: false,
        tags: [],
      });
      renderButton({
        scope: {all: [ASSET_DAILY]},
        preferredJobName: 'my_asset_job',
        launchMock,
      });
      await clickMaterializeButton();
      await screen.findByTestId('choose-partitions-dialog');

      // verify that checking "missing only" triggers the mutation with fewer partitions
      await userEvent.click(screen.getByTestId('missing-only-checkbox'));

      // verify that the executed mutation is correct
      await expectLaunchExecutesMutationAndCloses('Launch backfill', launchMock);
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
          assetCheckSelection: [],
          pipelineName: '__ASSET_JOB_7',
          repositoryLocationName: 'test.py',
          repositoryName: 'repo',
        },
      });
      renderButton({
        scope: {all: [ASSET_DAILY]},
        preferredJobName: undefined,
        launchMock,
      });
      await clickMaterializeButton();
      await screen.findByTestId('choose-partitions-dialog');
      await userEvent.click(await screen.findByTestId('latest-partition-button'));
      await expectLaunchExecutesMutationAndCloses('Launch 1 run', launchMock);
    });

    describe('Single run backfill toggle', () => {
      afterEach(() => {
        flagSpy.mockClear();
      });

      it('should launch backfills as pure-asset backfills if no job is in context', async () => {
        flagSpy.mockReturnValue(true);
        const launchMock = buildExpectedLaunchBackfillMutation({
          selector: undefined,
          assetSelection: [{path: ['asset_daily']}],
          partitionNames: ASSET_DAILY_PARTITION_KEYS,
          fromFailure: false,
          tags: [],
        });
        renderButton({
          scope: {all: [ASSET_DAILY]},
          preferredJobName: undefined,
          launchMock,
        });
        await clickMaterializeButton();
        await screen.findByTestId('choose-partitions-dialog');

        // missing-and-failed only option is available
        expect(screen.getByTestId('missing-only-checkbox')).toBeEnabled();

        // ranges-as-tags option is available
        const rangesAsTags = screen.getByTestId('ranges-as-tags-true-radio');
        await waitFor(async () => expect(rangesAsTags).toBeEnabled());

        await expectLaunchExecutesMutationAndCloses('Launch backfill', launchMock);
      });

      it('should launch a single run if you choose to pass the partition range using tags', async () => {
        flagSpy.mockReturnValue(true);
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
            assetCheckSelection: [],
          },
        });
        renderButton({
          scope: {all: [ASSET_DAILY]},
          preferredJobName: 'my_asset_job',
          launchMock,
        });
        await clickMaterializeButton();
        await screen.findByTestId('choose-partitions-dialog');

        const rangesAsTags = screen.getByTestId('ranges-as-tags-true-radio');
        await waitFor(async () => expect(rangesAsTags).toBeEnabled());
        await userEvent.click(rangesAsTags);
        await expectLaunchExecutesMutationAndCloses('Launch 1 run', launchMock);
      });

      it('should not show the backfill toggle if the flag is false', async () => {
        flagSpy.mockReturnValue(false);

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
            assetCheckSelection: [],
          },
        });
        renderButton({
          scope: {all: [ASSET_DAILY]},
          preferredJobName: 'my_asset_job',
          launchMock,
        });
        await clickMaterializeButton();
        await screen.findByTestId('choose-partitions-dialog');

        const rangesAsTags = screen.queryByTestId('ranges-as-tags-true-radio');
        expect(rangesAsTags).toBeNull();
      });
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

      renderButton({
        scope: {all: [ASSET_DAILY, ASSET_WEEKLY]},
        launchMock: LaunchMutationMock,
      });

      await clickMaterializeButton();

      // expect the dialog to be displayed
      await screen.findByTestId('choose-partitions-dialog');

      // expect the anchor asset to be labeled
      expect(screen.getByTestId('anchor-asset-label')).toHaveTextContent('asset_daily');

      // backfill options for run as tags, missing only are not available
      expect(screen.queryByTestId('missing-only-checkbox')).toBeNull();
      expect(screen.queryByTestId('ranges-as-tags-true-radio')).toBeNull();

      await expectLaunchExecutesMutationAndCloses('Launch backfill', LaunchMutationMock);
    });

    it('should offer a preview showing the exact ranges to be launched', async () => {
      const LaunchMutationMock = buildExpectedLaunchBackfillMutation({
        selector: undefined,
        assetSelection: [{path: ['asset_daily']}, {path: ['asset_weekly']}],
        partitionNames: ASSET_DAILY_PARTITION_KEYS,
        fromFailure: false,
        tags: [],
      });

      renderButton({
        scope: {all: [ASSET_DAILY, ASSET_WEEKLY]},
        launchMock: LaunchMutationMock,
      });

      await clickMaterializeButton();

      const preview = await screen.findByTestId('backfill-preview-button');
      await preview.click();

      // Expect the modal to be displayed. We have separate test coverage for
      // for the content of this modal
      await screen.findByTestId('backfill-preview-modal-content');
    });

    it('should offer to materialize all partitions if roots have different partition defintions ("pureAll" case)', async () => {
      const LaunchPureAllMutationMock = buildExpectedLaunchBackfillMutation({
        tags: [],
        assetSelection: [
          {path: ['asset_daily']},
          {path: ['asset_weekly']},
          {path: ['asset_weekly_root']},
        ],
        allPartitions: true,
      });

      await renderButton({
        scope: {all: [ASSET_DAILY, ASSET_WEEKLY, ASSET_WEEKLY_ROOT]},
        launchMock: LaunchPureAllMutationMock,
      });
      await clickMaterializeButton();

      // expect the dialog to be displayed
      await waitFor(() => screen.findByTestId('choose-partitions-dialog'));

      // expect the "all partitions only" warning and no anchor asset label
      expect(await screen.queryByTestId('anchor-asset-label')).toBeNull();
      expect(await screen.queryByTestId('pure-all-partitions-only')).toBeVisible();

      // backfill options for run as tags, missing only are not available
      expect(await screen.queryByTestId('missing-only-checkbox')).toBeNull();
      expect(await screen.queryByTestId('ranges-as-tags-true-radio')).toBeNull();

      await expectLaunchExecutesMutationAndCloses('Launch backfill', LaunchPureAllMutationMock);
    });
  });
});

// Helpers to make tests more concise

function renderButton({
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
    LaunchAssetLoaderResourceJob7Mock,
    LaunchAssetLoaderResourceJob8Mock,
    LaunchAssetLoaderResourceMyAssetJobMock,
    LaunchAssetCheckUpstreamWeeklyRootMock,
    ...PartitionHealthAssetMocks,
    buildLaunchAssetWarningsMock([]),
    buildConfigPartitionSelectionLatestPartitionMock('2020-01-02', 'my_asset_job_partition_set'),
    buildConfigPartitionSelectionLatestPartitionMock('2023-02-22', 'my_asset_job_partition_set'),
    buildConfigPartitionSelectionLatestPartitionMock('2023-02-22', '__ASSET_JOB_7_partition_set'),
    buildLaunchAssetLoaderMock(assetKeys),
    ...(launchMock ? [launchMock] : []),
  ];

  render(
    <TestProvider>
      <CustomAlertProvider />
      <MockedProvider mocks={mocks}>
        <LaunchAssetExecutionButton scope={scope} preferredJobName={preferredJobName} />
      </MockedProvider>
    </TestProvider>,
  );
}

async function clickMaterializeButton() {
  const materializeButton = await screen.findByTestId('materialize-button');
  expect(materializeButton).toBeVisible();
  await userEvent.click(materializeButton);
}

async function expectErrorShown(msg: string) {
  // expect an error to be displayed
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
  await userEvent.click(launchButton);

  // expect that it triggers the mutation (variables checked by mock matching)
  await waitFor(() => expect(mutation.result).toHaveBeenCalled());

  // expect the dialog to close
  await waitFor(() => {
    expect(screen.queryByTestId('choose-partitions-dialog')).toBeNull();
  });
}
