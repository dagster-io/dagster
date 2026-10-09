import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import dayjs from 'dayjs';
import {MemoryRouter} from 'react-router';

import {
  buildAddDynamicPartitionSuccess,
  buildAssetKey,
  buildAssetNode,
  buildDimensionDefinitionType,
  buildDimensionPartitionKeys,
  buildMultiPartitionStatuses,
  buildPartitionDefinition,
  buildTimePartitionRangeStatus,
  buildTimePartitionStatuses,
} from '../../graphql/builders';
import {PartitionDefinitionType, PartitionRangeStatus} from '../../graphql/types';
import {CREATE_PARTITION_MUTATION} from '../../partitions/CreatePartitionDialog';
import {
  AddDynamicPartitionMutation,
  AddDynamicPartitionMutationVariables,
} from '../../partitions/types/CreatePartitionDialog.types';
import {buildMutationMock, buildQueryMock, getMockResultFn} from '../../testing/mocking';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {buildWorkspaceMocks} from '../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {LaunchAssetChoosePartitionsDialog} from '../LaunchAssetChoosePartitionsDialog';
import {
  PartitionHealthQuery,
  PartitionHealthQueryVariables,
} from '../types/usePartitionHealthData.types';
import {PARTITION_HEALTH_QUERY} from '../usePartitionHealthData';

const workspaceMocks = buildWorkspaceMocks([]);

describe('launchAssetChoosePartitionsDialog', () => {
  it('Adding a dynamic partition when multiple assets selected', async () => {
    const assetA = buildAsset('asset_a', ['test']);
    const assetB = buildAsset('asset_b', ['test']);

    const assetAQueryMock = buildQueryMock<PartitionHealthQuery, PartitionHealthQueryVariables>({
      query: PARTITION_HEALTH_QUERY,
      variables: {assetKey: {path: ['asset_a']}},
      data: {assetNodeOrError: assetA},
    });
    const assetBQueryMock = buildQueryMock<PartitionHealthQuery, PartitionHealthQueryVariables>({
      query: PARTITION_HEALTH_QUERY,
      variables: {assetKey: {path: ['asset_b']}},
      data: {assetNodeOrError: assetB},
    });
    const assetASecondQueryMock = buildQueryMock<
      PartitionHealthQuery,
      PartitionHealthQueryVariables
    >({
      query: PARTITION_HEALTH_QUERY,
      variables: {assetKey: {path: ['asset_a']}},
      data: {assetNodeOrError: buildAsset('asset_a', ['test', 'test2'])},
    });
    const assetBSecondQueryMock = buildQueryMock<
      PartitionHealthQuery,
      PartitionHealthQueryVariables
    >({
      query: PARTITION_HEALTH_QUERY,
      variables: {assetKey: {path: ['asset_b']}},
      data: {assetNodeOrError: buildAsset('asset_b', ['test', 'test2'])},
      delay: 5000,
    });

    const addPartitionMock = buildMutationMock<
      AddDynamicPartitionMutation,
      AddDynamicPartitionMutationVariables
    >({
      query: CREATE_PARTITION_MUTATION,
      variables: {
        repositorySelector: {repositoryName: 'test', repositoryLocationName: 'test'},
        partitionsDefName: 'foo',
        partitionKey: 'test2',
      },
      data: {
        addDynamicPartition: buildAddDynamicPartitionSuccess(),
      },
    });

    const assetAQueryMockResult = getMockResultFn(assetAQueryMock);
    const assetBQueryMockResult = getMockResultFn(assetBQueryMock);
    const assetASecondQueryMockResult = getMockResultFn(assetASecondQueryMock);
    const assetBSecondQueryMockResult = getMockResultFn(assetBSecondQueryMock);
    render(
      <MemoryRouter>
        <MockedProvider
          mocks={[
            assetAQueryMock,
            assetBQueryMock,
            assetASecondQueryMock,
            assetBSecondQueryMock,
            addPartitionMock,
            ...workspaceMocks,
          ]}
        >
          <WorkspaceProvider>
            <LaunchAssetChoosePartitionsDialog
              open={true}
              setOpen={(_open: boolean) => {}}
              repoAddress={buildRepoAddress('test', 'test')}
              target={{
                jobName: '__ASSET_JOB',
                assetKeys: [assetA.assetKey, assetB.assetKey],
                type: 'job',
              }}
              assets={[assetA, assetB]}
              upstreamAssetKeys={[]}
            />
          </WorkspaceProvider>
        </MockedProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(assetAQueryMockResult).toHaveBeenCalled();
      expect(assetBQueryMockResult).toHaveBeenCalled();
    });

    const link = await screen.findByTestId('add-partition-link');
    await userEvent.click(link);
    const partitionInput = await screen.findByTestId('partition-input');
    await userEvent.type(partitionInput, 'test2');
    expect(assetASecondQueryMockResult).not.toHaveBeenCalled();
    expect(assetBSecondQueryMockResult).not.toHaveBeenCalled();
    const savePartitionButton = screen.getByTestId('save-partition-button');
    await userEvent.click(savePartitionButton);

    // Verify that it refreshes asset health after partition is added
    await waitFor(() => {
      expect(assetASecondQueryMockResult).toHaveBeenCalled();
    });
  });

  it('hides partitions outside the default date window and offers to reveal them', async () => {
    const asset = buildDailyAsset('asset_daily', [...OLD_PARTITION_KEYS, ...RECENT_PARTITION_KEYS]);
    const healthMock = buildQueryMock<PartitionHealthQuery, PartitionHealthQueryVariables>({
      query: PARTITION_HEALTH_QUERY,
      variables: {assetKey: {path: ['asset_daily']}},
      data: {assetNodeOrError: asset},
    });

    render(
      <MemoryRouter>
        <MockedProvider mocks={[healthMock, ...workspaceMocks]}>
          <WorkspaceProvider>
            <LaunchAssetChoosePartitionsDialog
              open={true}
              setOpen={(_open: boolean) => {}}
              repoAddress={buildRepoAddress('test', 'test')}
              target={{jobName: '__ASSET_JOB', assetKeys: [asset.assetKey], type: 'job'}}
              assets={[asset]}
              upstreamAssetKeys={[]}
            />
          </WorkspaceProvider>
        </MockedProvider>
      </MemoryRouter>,
    );

    const notice = await screen.findByTestId('hidden-partitions-notice');
    expect(notice).toHaveTextContent(`${OLD_PARTITION_KEYS.length} older partitions`);

    // "All" covers only what's visible.
    await userEvent.click(await screen.findByTestId('all-partition-button'));
    expect(await screen.findByText(`${RECENT_PARTITION_KEYS.length} partitions`)).toBeVisible();

    await userEvent.click(await screen.findByTestId('show-all-partitions-link'));
    await waitFor(() => {
      expect(screen.queryByTestId('hidden-partitions-notice')).toBeNull();
    });

    await userEvent.click(await screen.findByTestId('all-partition-button'));
    const total = OLD_PARTITION_KEYS.length + RECENT_PARTITION_KEYS.length;
    expect(await screen.findByText(`${total} partitions`)).toBeVisible();
  });
  it('selects only missing partitions inside the default date window', async () => {
    // Every recent partition is materialized; only the hidden, older ones are missing.
    const asset = buildDailyAsset(
      'asset_daily',
      [...OLD_PARTITION_KEYS, ...RECENT_PARTITION_KEYS],
      [
        buildTimePartitionRangeStatus({
          startKey: RECENT_PARTITION_KEYS[0],
          endKey: RECENT_PARTITION_KEYS[RECENT_PARTITION_KEYS.length - 1],
          status: PartitionRangeStatus.MATERIALIZED,
        }),
      ],
    );
    const healthMock = buildQueryMock<PartitionHealthQuery, PartitionHealthQueryVariables>({
      query: PARTITION_HEALTH_QUERY,
      variables: {assetKey: {path: ['asset_daily']}},
      data: {assetNodeOrError: asset},
    });

    render(
      <MemoryRouter>
        <MockedProvider mocks={[healthMock, ...workspaceMocks]}>
          <WorkspaceProvider>
            <LaunchAssetChoosePartitionsDialog
              open={true}
              setOpen={(_open: boolean) => {}}
              repoAddress={buildRepoAddress('test', 'test')}
              target={{jobName: '__ASSET_JOB', assetKeys: [asset.assetKey], type: 'job'}}
              assets={[asset]}
              upstreamAssetKeys={[]}
            />
          </WorkspaceProvider>
        </MockedProvider>
      </MemoryRouter>,
    );

    await screen.findByTestId('hidden-partitions-notice');

    await userEvent.click(await screen.findByTestId('all-partition-button'));
    expect(await screen.findByText(`${RECENT_PARTITION_KEYS.length} partitions`)).toBeVisible();

    await userEvent.click(await screen.findByRole('button', {name: 'Missing'}));
    expect(await screen.findByText('0 partitions')).toBeVisible();
  });
});

function buildAsset(name: string, dynamicPartitionKeys: string[]) {
  return buildAssetNode({
    assetKey: buildAssetKey({path: [name]}),
    id: `repro_dynamic_in_multipartitions_bug.py.__repository__.["${name}"]`,
    partitionKeysByDimension: [
      buildDimensionPartitionKeys({
        name: 'a',
        type: PartitionDefinitionType.DYNAMIC,
        partitionKeys: dynamicPartitionKeys,
      }),
      buildDimensionPartitionKeys({
        name: 'b',
        type: PartitionDefinitionType.TIME_WINDOW,
        partitionKeys: ['2024-01-01'],
      }),
    ],
    partitionDefinition: buildPartitionDefinition({
      name: 'not-foo',
      dimensionTypes: [
        buildDimensionDefinitionType({
          name: 'a',
          type: PartitionDefinitionType.DYNAMIC,
          dynamicPartitionsDefinitionName: 'foo',
        }),
        buildDimensionDefinitionType({
          name: 'b',
          type: PartitionDefinitionType.TIME_WINDOW,
        }),
      ],
    }),
    assetPartitionStatuses: buildMultiPartitionStatuses({
      primaryDimensionName: 'b',
      ranges: [],
    }),
  });
}

const dailyKeys = (start: dayjs.Dayjs, count: number) =>
  Array.from({length: count}, (_, i) => start.add(i, 'day').format('YYYY-MM-DD'));

// Comfortably outside and inside the default window, so the split doesn't shift
// with the machine's timezone.
const OLD_PARTITION_KEYS = dailyKeys(dayjs().subtract(2, 'year'), 30);
const RECENT_PARTITION_KEYS = dailyKeys(dayjs().subtract(9, 'day'), 10);

function buildDailyAsset(
  name: string,
  partitionKeys: string[],
  ranges: ReturnType<typeof buildTimePartitionRangeStatus>[] = [],
) {
  return buildAssetNode({
    assetKey: buildAssetKey({path: [name]}),
    id: `daily.py.__repository__.["${name}"]`,
    partitionKeysByDimension: [
      buildDimensionPartitionKeys({
        name: 'default',
        type: PartitionDefinitionType.TIME_WINDOW,
        partitionKeys,
      }),
    ],
    partitionDefinition: buildPartitionDefinition({
      name: 'daily',
      dimensionTypes: [
        buildDimensionDefinitionType({name: 'default', type: PartitionDefinitionType.TIME_WINDOW}),
      ],
    }),
    assetPartitionStatuses: buildTimePartitionStatuses({ranges}),
  });
}
