import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import React from 'react';

import {LAUNCH_PARTITION_BACKFILL_MUTATION} from '../instance/BackfillUtils';
import {LaunchPartitionBackfillMutation} from '../instance/types/BackfillUtils.types';
import {TestProvider} from '../testing/TestProvider';

import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {
  ASSET_DAILY,
  ASSET_DAILY_PARTITION_KEYS,
  ASSET_WEEKLY,
  LaunchAssetChoosePartitionsMock,
  LaunchAssetLoaderAssetDailyWeeklyMock,
  PartitionHealthAssetDailyMock,
  PartitionHealthAssetWeeklyMock,
} from './LaunchAssetExecutionButton.mocks';

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../graph/asyncGraphLayout', () => ({}));

describe('LaunchAssetExecutionButton', () => {
  it('should show the partition dialog with an anchor asset', async () => {
    const LaunchMutationMock: MockedResponse<LaunchPartitionBackfillMutation> = {
      request: {
        query: LAUNCH_PARTITION_BACKFILL_MUTATION,
        variables: {
          backfillParams: {
            selector: undefined,
            assetSelection: [{path: ['asset_daily']}, {path: ['asset_weekly']}],
            partitionNames: ASSET_DAILY_PARTITION_KEYS,
            fromFailure: false,
            tags: [],
          },
        },
      },
      result: jest.fn(() => ({
        data: {
          __typename: 'DagitMutation',
          launchPartitionBackfill: {__typename: 'LaunchBackfillSuccess', backfillId: 'vlpmimsl'},
        },
      })),
    };

    await act(async () => {
      render(
        <TestProvider>
          <MockedProvider
            mocks={[
              LaunchAssetChoosePartitionsMock,
              LaunchAssetLoaderAssetDailyWeeklyMock,
              PartitionHealthAssetDailyMock,
              PartitionHealthAssetWeeklyMock,
              LaunchMutationMock,
            ]}
          >
            <LaunchAssetExecutionButton scope={{all: [ASSET_DAILY, ASSET_WEEKLY]}} />
          </MockedProvider>
        </TestProvider>,
      );
    });

    // click Materialize
    const materializeButton = await screen.findByTestId('materialize-button');
    expect(materializeButton).toBeVisible();
    materializeButton.click();

    // expect the dialog to be displayed
    await waitFor(async () => {
      await screen.findByTestId('choose-partitions-dialog');
    });

    // expect the anchor asset label to be present, and the missing + tags options to be hidden
    expect((await screen.findByTestId('anchor-asset-label')).textContent).toEqual('asset_daily');
    expect(await screen.queryByTestId('missing-only-checkbox')).toBeNull();
    expect(await screen.queryByTestId('ranges-as-tags-checkbox')).toBeNull();

    const launchButton = await screen.findByTestId('launch-button');
    expect(launchButton.textContent).toEqual('Launch Backfill');
    await launchButton.click();

    // expect that it triggers the mutation (variables checked by mock matching)
    await waitFor(async () => {
      expect(LaunchMutationMock.result).toHaveBeenCalled();
    });

    // expect the dialog to close
    await waitFor(async () => {
      expect(await screen.queryByTestId('choose-partitions-dialog')).toBeNull();
    });
  });
});
