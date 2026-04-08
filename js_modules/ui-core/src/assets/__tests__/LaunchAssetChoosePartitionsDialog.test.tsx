import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router';

import {
  buildAddDynamicPartitionSuccess,
  buildAssetKey,
  buildAssetNode,
  buildDimensionDefinitionType,
  buildDimensionPartitionKeys,
  buildMultiPartitionStatuses,
  buildPartitionDefinition,
  buildPartitionKeyLabel,
  buildPartitionSets,
  buildPipeline,
  buildQuery,
  buildRunConfigSchema,
} from '../../graphql/builders';
import {PartitionDefinitionType} from '../../graphql/types';
import {PIPELINE_EXECUTION_ROOT_QUERY} from '../../launchpad/LaunchpadAllowedRoot';
import {
  LaunchpadRootQuery,
  LaunchpadRootQueryVariables,
} from '../../launchpad/types/LaunchpadAllowedRoot.types';
import {CREATE_PARTITION_MUTATION} from '../../partitions/CreatePartitionDialog';
import {
  AddDynamicPartitionMutation,
  AddDynamicPartitionMutationVariables,
} from '../../partitions/types/CreatePartitionDialog.types';
import {
  buildMutationMock,
  buildQueryMock,
  getMockResultFn,
  mockViewportClientRect,
  restoreViewportClientRect,
} from '../../testing/mocking';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {buildWorkspaceMocks} from '../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {
  DISPLAYED_PARTITION_LABELS_QUERY,
  LaunchAssetChoosePartitionsDialog,
} from '../LaunchAssetChoosePartitionsDialog';
import {buildLaunchAssetWarningsMock} from '../__fixtures__/LaunchAssetExecutionButton.fixtures';
import {NoRunningBackfills} from '../__fixtures__/RunningBackfillsNoticeQuery.fixture';
import {
  AssetsPermissionsQuery,
  AssetsPermissionsQueryVariables,
} from '../types/useAssetPermissions.types';
import {
  PartitionHealthQuery,
  PartitionHealthQueryVariables,
} from '../types/usePartitionHealthData.types';
import {ASSETS_PERMISSIONS_QUERY} from '../useAssetPermissions';
import {PARTITION_HEALTH_QUERY} from '../usePartitionHealthData';

const workspaceMocks = buildWorkspaceMocks([]);
describe('launchAssetChoosePartitionsDialog', () => {
  beforeAll(() => {
    mockViewportClientRect();
  });

  afterAll(() => {
    restoreViewportClientRect();
  });

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

  it('renders and searches dynamic partition labels in the selector', async () => {
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
    const displayedPartitionLabelsMock = buildQueryMock({
      query: DISPLAYED_PARTITION_LABELS_QUERY,
      variables: {assetKey: {path: ['asset_a']}},
      data: {
        assetNodeOrError: buildAssetNode({
          id: assetA.id,
          partitionKeyLabels: [buildPartitionKeyLabel({key: 'test', label: 'Friendly label'})],
        }),
      },
    });
    const assetAQueryMockResult = getMockResultFn(assetAQueryMock);
    const assetBQueryMockResult = getMockResultFn(assetBQueryMock);
    const assetPermissionsMock = buildQueryMock<
      AssetsPermissionsQuery,
      AssetsPermissionsQueryVariables
    >({
      query: ASSETS_PERMISSIONS_QUERY,
      variables: {
        assetKeys: [{path: ['asset_a']}, {path: ['asset_b']}],
      },
      data: {
        assetNodes: [
          buildAssetNode({
            id: 'asset-a-permissions',
            hasMaterializePermission: true,
            hasWipePermission: true,
            hasReportRunlessAssetEventPermission: true,
          }),
          buildAssetNode({
            id: 'asset-b-permissions',
            hasMaterializePermission: true,
            hasWipePermission: true,
            hasReportRunlessAssetEventPermission: true,
          }),
        ],
      },
    });
    const launchpadRootMock = buildQueryMock<LaunchpadRootQuery, LaunchpadRootQueryVariables>({
      query: PIPELINE_EXECUTION_ROOT_QUERY,
      variables: {
        repositoryName: 'test',
        repositoryLocationName: 'test',
        pipelineName: '__ASSET_JOB',
        assetSelection: [{path: ['asset_a']}, {path: ['asset_b']}],
      },
      data: buildQuery({
        pipelineOrError: buildPipeline(),
        partitionSetsOrError: buildPartitionSets(),
        runConfigSchemaOrError: buildRunConfigSchema(),
      }),
    });

    render(
      <MemoryRouter>
        <MockedProvider
          mocks={[
            assetAQueryMock,
            assetBQueryMock,
            displayedPartitionLabelsMock,
            assetPermissionsMock,
            buildLaunchAssetWarningsMock([]),
            NoRunningBackfills,
            launchpadRootMock,
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

    const user = userEvent.setup();
    await waitFor(() => {
      expect(assetAQueryMockResult).toHaveBeenCalled();
      expect(assetBQueryMockResult).toHaveBeenCalled();
    });

    await user.click(await screen.findByText('Select a partition or create one'));

    expect((await screen.findByTestId('menu-item-test')).textContent).toContain('Friendly label');

    const searchInput = await screen.findByPlaceholderText('Filter partitions');
    await user.type(searchInput, 'Friendly');

    expect((await screen.findByTestId('menu-item-test')).textContent).toContain('Friendly label');
  });
});

function buildAsset(
  name: string,
  dynamicPartitionKeys: string[],
  partitionKeyLabels: Array<{__typename: 'PartitionKeyLabel'; key: string; label: string}> = [],
) {
  return buildAssetNode({
    assetKey: buildAssetKey({path: [name]}),
    id: `repro_dynamic_in_multipartitions_bug.py.__repository__.["${name}"]`,
    partitionKeyLabels,
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
