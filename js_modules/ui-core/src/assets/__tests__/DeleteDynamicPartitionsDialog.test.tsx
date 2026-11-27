import {MockedProvider} from '@apollo/client/testing';
import {screen, waitFor} from '@testing-library/dom';
import {render} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {useContext} from 'react';

import {CloudOSSContext} from '../../app/CloudOSSContext';
import {
  buildAssetNode,
  buildDeleteDynamicPartitionsSuccess,
  buildMutation,
} from '../../graphql/builders';
import {TestPermissionsProvider} from '../../testing/TestPermissions';
import {
  buildQueryMock,
  mockViewportClientRect,
  restoreViewportClientRect,
} from '../../testing/mocking';
import {
  DELETE_DYNAMIC_PARTITIONS_MUTATION,
  DeleteDynamicPartitionsDialog,
} from '../DeleteDynamicPartitionsDialog';
import {ONE_DIMENSIONAL_DYNAMIC_ASSET} from '../__fixtures__/PartitionHealth.fixtures';
import {
  AssetsPermissionsQuery,
  AssetsPermissionsQueryVariables,
} from '../types/useAssetPermissions.types';
import {ASSETS_PERMISSIONS_QUERY} from '../useAssetPermissions';
import {PARTITION_HEALTH_QUERY} from '../usePartitionHealthData';

const WipeOnDeleteFeature = ({
  canWipeAssets,
  children,
}: {
  canWipeAssets: boolean;
  children: React.ReactNode;
}) => {
  const value = useContext(CloudOSSContext);
  return (
    <CloudOSSContext.Provider
      value={{
        ...value,
        featureContext: {...value.featureContext, canWipeOnDeleteDynamicPartitions: true},
      }}
    >
      <TestPermissionsProvider
        unscopedOverrides={{canWipeAssets: {enabled: canWipeAssets, disabledReason: ''}}}
      >
        {children}
      </TestPermissionsProvider>
    </CloudOSSContext.Provider>
  );
};

const WipeOnDeleteWithLocationPermission = ({children}: {children: React.ReactNode}) => (
  <WipeOnDeleteFeature canWipeAssets>{children}</WipeOnDeleteFeature>
);

const WipeOnDeleteWithoutLocationPermission = ({children}: {children: React.ReactNode}) => (
  <WipeOnDeleteFeature canWipeAssets={false}>{children}</WipeOnDeleteFeature>
);

const buildDeletePartitionsMock = (wipeMaterializations: boolean) => ({
  request: {
    query: DELETE_DYNAMIC_PARTITIONS_MUTATION,
    variables: {
      repositorySelector: {repositoryLocationName: 'location', repositoryName: 'repo.py'},
      partitionsDefName: 'fruits',
      partitionKeys: ['apple', 'fig'],
      wipeMaterializations,
    },
  },
  result: jest.fn(() => ({
    data: buildMutation({
      deleteDynamicPartitions: buildDeleteDynamicPartitionsSuccess(),
    }),
  })),
});

const renderDialog = (
  deletePartitionsMock: ReturnType<typeof buildDeletePartitionsMock>,
  {
    wrapper,
    hasWipePermission = true,
  }: {
    wrapper?: React.ComponentType<{children: React.ReactNode}>;
    hasWipePermission?: boolean;
  } = {},
) => {
  render(
    <MockedProvider
      mocks={[
        buildQueryMock({
          query: PARTITION_HEALTH_QUERY,
          variables: {assetKey: {path: ['asset']}},
          data: ONE_DIMENSIONAL_DYNAMIC_ASSET,
        }),
        buildQueryMock<AssetsPermissionsQuery, AssetsPermissionsQueryVariables>({
          query: ASSETS_PERMISSIONS_QUERY,
          variables: {assetKeys: [{path: ['asset']}]},
          data: {assetNodes: [buildAssetNode({id: 'asset-permissions', hasWipePermission})]},
        }),
        deletePartitionsMock,
      ]}
    >
      <DeleteDynamicPartitionsDialog
        assetKey={{path: ['asset']}}
        repoAddress={{location: 'location', name: 'repo.py'}}
        partitionsDefName="fruits"
        isOpen
        onClose={() => {}}
      />
    </MockedProvider>,
    {wrapper},
  );
};

const selectPartitionsAndDelete = async (user: ReturnType<typeof userEvent.setup>) => {
  await waitFor(() => {
    expect(screen.getByText('Delete fruits partitions')).toBeVisible();
  });

  const selectPartition = await screen.findByText('Select a partition');
  await user.click(selectPartition);

  await user.click(await screen.findByTestId('menu-item-apple'));
  await user.click(await screen.findByTestId(`menu-item-fig`));

  await user.click(await screen.findByText(/delete 2 partitions/i));
};

describe('DeleteDynamicPartitionsDialog', () => {
  beforeAll(() => {
    mockViewportClientRect();
  });
  afterAll(() => {
    restoreViewportClientRect();
  });

  it('should show a partition selector and delete selected partitions', async () => {
    const user = userEvent.setup();
    const deletePartitionsMock = buildDeletePartitionsMock(false);

    renderDialog(deletePartitionsMock);

    await selectPartitionsAndDelete(user);

    expect(deletePartitionsMock.result).toHaveBeenCalled();
    expect(screen.queryByText(/also wipe materialization events/i)).toBeNull();
  });

  it('should wipe materializations when the wipe-on-delete feature is enabled', async () => {
    const user = userEvent.setup();
    const deletePartitionsMock = buildDeletePartitionsMock(true);

    renderDialog(deletePartitionsMock, {wrapper: WipeOnDeleteWithLocationPermission});

    // the checkbox renders and defaults to checked
    const checkbox = await screen.findByRole('checkbox');
    expect(checkbox).toBeChecked();

    await selectPartitionsAndDelete(user);

    expect(deletePartitionsMock.result).toHaveBeenCalled();
  });

  it('should not wipe materializations when the checkbox is unchecked', async () => {
    const user = userEvent.setup();
    const deletePartitionsMock = buildDeletePartitionsMock(false);

    renderDialog(deletePartitionsMock, {wrapper: WipeOnDeleteWithLocationPermission});

    await user.click(await screen.findByRole('checkbox'));
    expect(screen.getByRole('checkbox')).not.toBeChecked();

    await selectPartitionsAndDelete(user);

    expect(deletePartitionsMock.result).toHaveBeenCalled();
  });

  it('should not offer to wipe materializations without the asset wipe permission', async () => {
    const user = userEvent.setup();
    const deletePartitionsMock = buildDeletePartitionsMock(false);

    renderDialog(deletePartitionsMock, {
      wrapper: WipeOnDeleteWithLocationPermission,
      hasWipePermission: false,
    });

    await waitFor(() => {
      expect(screen.getByRole('checkbox')).toBeDisabled();
    });
    expect(screen.getByRole('checkbox')).not.toBeChecked();

    await selectPartitionsAndDelete(user);

    expect(deletePartitionsMock.result).toHaveBeenCalled();
  });

  it('should offer to wipe materializations with only the asset wipe permission', async () => {
    const user = userEvent.setup();
    const deletePartitionsMock = buildDeletePartitionsMock(true);

    renderDialog(deletePartitionsMock, {wrapper: WipeOnDeleteWithoutLocationPermission});

    await waitFor(() => {
      expect(screen.getByRole('checkbox')).toBeEnabled();
    });
    expect(screen.getByRole('checkbox')).toBeChecked();

    await selectPartitionsAndDelete(user);

    expect(deletePartitionsMock.result).toHaveBeenCalled();
  });
});
