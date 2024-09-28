import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import {MemoryRouter} from 'react-router';

import {
  PartitionDefinitionType,
  buildAddDynamicPartitionSuccess,
  buildAssetKey,
  buildAssetNode,
  buildDimensionDefinitionType,
  buildDimensionPartitionKeys,
  buildMultiPartitionStatuses,
  buildPartitionDefinition,
} from '../../graphql/types';
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

    const link = await waitFor(() => screen.getByTestId('add-partition-link'));
    userEvent.click(link);
    const partitionInput = await waitFor(() => screen.getByTestId('partition-input'));
    await userEvent.type(partitionInput, 'test2');
    expect(assetASecondQueryMockResult).not.toHaveBeenCalled();
    expect(assetBSecondQueryMockResult).not.toHaveBeenCalled();
    const savePartitionButton = screen.getByTestId('save-partition-button');
    userEvent.click(savePartitionButton);

    // Verify that it refreshes asset health after partition is added
    await waitFor(() => {
      expect(assetASecondQueryMockResult).toHaveBeenCalled();
    });
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
