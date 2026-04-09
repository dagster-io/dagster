import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor, within} from '@testing-library/react';
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
    const displayedPartitionLabelsMock = buildQueryMock({
      query: DISPLAYED_PARTITION_LABELS_QUERY,
      variables: {assetKey: {path: ['asset_a']}},
      data: {
        assetNodeOrError: {
          __typename: 'AssetNode',
          id: assetA.id,
          partitionKeyLabels: [],
        },
      },
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
            assetASecondQueryMock,
            assetBSecondQueryMock,
            displayedPartitionLabelsMock,
            addPartitionMock,
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

    const link = await screen.findByTestId('add-partition-link');
    await user.click(link);
    const partitionInput = await screen.findByTestId('partition-input');
    await user.type(partitionInput, 'test2');
    expect(assetASecondQueryMockResult).not.toHaveBeenCalled();
    expect(assetBSecondQueryMockResult).not.toHaveBeenCalled();
    const savePartitionButton = screen.getByTestId('save-partition-button');
    await user.click(savePartitionButton);

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
        assetNodeOrError: {
          __typename: 'AssetNode',
          id: assetA.id,
          partitionKeyLabels: [
            {__typename: 'PartitionKeyLabel', key: 'test', label: 'Friendly label'},
          ],
        },
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

  it('clears stale labels when the displayed asset changes while labels are still loading', async () => {
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
    const displayedPartitionLabelsMockA = buildQueryMock({
      query: DISPLAYED_PARTITION_LABELS_QUERY,
      variables: {assetKey: {path: ['asset_a']}},
      data: {
        assetNodeOrError: {
          __typename: 'AssetNode',
          id: assetA.id,
          partitionKeyLabels: [
            {__typename: 'PartitionKeyLabel', key: 'test', label: 'Alpha label'},
          ],
        },
      },
    });
    const displayedPartitionLabelsMockB = buildQueryMock({
      query: DISPLAYED_PARTITION_LABELS_QUERY,
      variables: {assetKey: {path: ['asset_b']}},
      data: {
        assetNodeOrError: {
          __typename: 'AssetNode',
          id: assetB.id,
          partitionKeyLabels: [{__typename: 'PartitionKeyLabel', key: 'test', label: 'Beta label'}],
        },
      },
      delay: 5000,
    });
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
    const reversedAssetPermissionsMock = buildQueryMock<
      AssetsPermissionsQuery,
      AssetsPermissionsQueryVariables
    >({
      query: ASSETS_PERMISSIONS_QUERY,
      variables: {
        assetKeys: [{path: ['asset_b']}, {path: ['asset_a']}],
      },
      data: {
        assetNodes: [
          buildAssetNode({
            id: 'asset-b-permissions-reordered',
            hasMaterializePermission: true,
            hasWipePermission: true,
            hasReportRunlessAssetEventPermission: true,
          }),
          buildAssetNode({
            id: 'asset-a-permissions-reordered',
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
    const reversedLaunchpadRootMock = buildQueryMock<
      LaunchpadRootQuery,
      LaunchpadRootQueryVariables
    >({
      query: PIPELINE_EXECUTION_ROOT_QUERY,
      variables: {
        repositoryName: 'test',
        repositoryLocationName: 'test',
        pipelineName: '__ASSET_JOB',
        assetSelection: [{path: ['asset_b']}, {path: ['asset_a']}],
      },
      data: buildQuery({
        pipelineOrError: buildPipeline(),
        partitionSetsOrError: buildPartitionSets(),
        runConfigSchemaOrError: buildRunConfigSchema(),
      }),
    });

    const {rerender} = render(
      <MemoryRouter>
        <MockedProvider
          mocks={[
            assetAQueryMock,
            assetBQueryMock,
            displayedPartitionLabelsMockA,
            displayedPartitionLabelsMockB,
            assetPermissionsMock,
            reversedAssetPermissionsMock,
            buildLaunchAssetWarningsMock([]),
            NoRunningBackfills,
            launchpadRootMock,
            reversedLaunchpadRootMock,
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
    await user.click(await screen.findByText('Select a partition or create one'));
    await waitFor(() => {
      expect(screen.getByTestId('menu-item-test').textContent).toContain('Alpha label');
    });

    rerender(
      <MemoryRouter>
        <MockedProvider
          mocks={[
            assetAQueryMock,
            assetBQueryMock,
            displayedPartitionLabelsMockA,
            displayedPartitionLabelsMockB,
            assetPermissionsMock,
            reversedAssetPermissionsMock,
            buildLaunchAssetWarningsMock([]),
            NoRunningBackfills,
            launchpadRootMock,
            reversedLaunchpadRootMock,
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
              assets={[assetB, assetA]}
              upstreamAssetKeys={[]}
            />
          </WorkspaceProvider>
        </MockedProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('menu-item-test').textContent).not.toContain('Alpha label');
    });
  });

  it('does not apply dynamic labels to non-dynamic dimensions with overlapping keys', async () => {
    const asset = buildAsset('asset_a', ['shared'], [], {
      type: PartitionDefinitionType.STATIC,
      keys: ['shared', 'plain'],
    });

    const assetQueryMock = buildQueryMock<PartitionHealthQuery, PartitionHealthQueryVariables>({
      query: PARTITION_HEALTH_QUERY,
      variables: {assetKey: {path: ['asset_a']}},
      data: {assetNodeOrError: asset},
    });
    const displayedPartitionLabelsMock = buildQueryMock({
      query: DISPLAYED_PARTITION_LABELS_QUERY,
      variables: {assetKey: {path: ['asset_a']}},
      data: {
        assetNodeOrError: {
          __typename: 'AssetNode',
          id: asset.id,
          partitionKeyLabels: [
            {__typename: 'PartitionKeyLabel', key: 'shared', label: 'Friendly label'},
          ],
        },
      },
    });
    const assetPermissionsMock = buildQueryMock<
      AssetsPermissionsQuery,
      AssetsPermissionsQueryVariables
    >({
      query: ASSETS_PERMISSIONS_QUERY,
      variables: {
        assetKeys: [{path: ['asset_a']}],
      },
      data: {
        assetNodes: [
          buildAssetNode({
            id: 'asset-a-permissions',
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
        assetSelection: [{path: ['asset_a']}],
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
            assetQueryMock,
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
                assetKeys: [asset.assetKey],
                type: 'job',
              }}
              assets={[asset]}
              upstreamAssetKeys={[]}
            />
          </WorkspaceProvider>
        </MockedProvider>
      </MemoryRouter>,
    );

    const user = userEvent.setup();
    const selectors = await screen.findAllByText('Select a partition or create one');
    expect(selectors).toHaveLength(2);

    const dynamicSelector = selectors[0];
    const staticSelector = selectors[1];

    if (!dynamicSelector || !staticSelector) {
      throw new Error('Expected both dynamic and static partition selectors to be rendered');
    }

    await user.click(dynamicSelector);
    await waitFor(() => {
      expect(screen.getByTestId('menu-item-shared').textContent).toContain('Friendly label');
    });

    await user.click(staticSelector);
    const searchInput = await screen.findByPlaceholderText('Filter partitions');
    await user.type(searchInput, 'Friendly');

    const staticMenu = searchInput.closest('[role="menu"]');
    expect(staticMenu).not.toBeNull();
    expect(
      within(staticMenu as HTMLElement).getByText('No matching partitions found'),
    ).toBeVisible();
  });
});

function buildAsset(
  name: string,
  dynamicPartitionKeys: string[],
  partitionKeyLabels: Array<{__typename: 'PartitionKeyLabel'; key: string; label: string}> = [],
  secondDimension: {
    type: PartitionDefinitionType;
    keys: string[];
  } = {type: PartitionDefinitionType.TIME_WINDOW, keys: ['2024-01-01']},
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
        type: secondDimension.type,
        partitionKeys: secondDimension.keys,
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
          type: secondDimension.type,
        }),
      ],
    }),
    assetPartitionStatuses: buildMultiPartitionStatuses({
      primaryDimensionName: 'b',
      ranges: [],
    }),
  });
}
