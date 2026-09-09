import {MockedProvider} from '@apollo/client/testing';
import {screen, waitFor} from '@testing-library/dom';
import {render} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {useContext} from 'react';

import {CloudOSSContext} from '../../app/CloudOSSContext';
import {buildDeleteDynamicPartitionsSuccess, buildMutation} from '../../graphql/builders';
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
import {PARTITION_HEALTH_QUERY} from '../usePartitionHealthData';

const WipeOnDeleteEnabled = ({children}: {children: React.ReactNode}) => {
  const value = useContext(CloudOSSContext);
  return (
    <CloudOSSContext.Provider
      value={{
        ...value,
        featureContext: {...value.featureContext, canWipeOnDeleteDynamicPartitions: true},
      }}
    >
      {children}
    </CloudOSSContext.Provider>
  );
};

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
  wrapper?: React.ComponentType<{children: React.ReactNode}>,
) => {
  render(
    <MockedProvider
      mocks={[
        buildQueryMock({
          query: PARTITION_HEALTH_QUERY,
          variables: {assetKey: {path: ['asset']}},
          data: ONE_DIMENSIONAL_DYNAMIC_ASSET,
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

    renderDialog(deletePartitionsMock, WipeOnDeleteEnabled);

    // the checkbox renders and defaults to checked
    const checkbox = await screen.findByRole('checkbox');
    expect(checkbox).toBeChecked();

    await selectPartitionsAndDelete(user);

    expect(deletePartitionsMock.result).toHaveBeenCalled();
  });

  it('should not wipe materializations when the checkbox is unchecked', async () => {
    const user = userEvent.setup();
    const deletePartitionsMock = buildDeletePartitionsMock(false);

    renderDialog(deletePartitionsMock, WipeOnDeleteEnabled);

    await user.click(await screen.findByRole('checkbox'));
    expect(screen.getByRole('checkbox')).not.toBeChecked();

    await selectPartitionsAndDelete(user);

    expect(deletePartitionsMock.result).toHaveBeenCalled();
  });
});
