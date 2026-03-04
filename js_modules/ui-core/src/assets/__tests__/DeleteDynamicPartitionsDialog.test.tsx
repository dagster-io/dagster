import {MockedProvider} from '@apollo/client/testing';
import {screen, waitFor} from '@testing-library/dom';
import {render} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {buildDeleteDynamicPartitionsSuccess, buildMutation} from '../../graphql/types';
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

describe('DeleteDynamicPartitionsDialog', () => {
  beforeAll(() => {
    mockViewportClientRect();
  });
  afterAll(() => {
    restoreViewportClientRect();
  });

  it('should show a partition selector and delete selected partitions', async () => {
    const user = userEvent.setup();

    const deletePartitionsMock = {
      request: {
        query: DELETE_DYNAMIC_PARTITIONS_MUTATION,
        variables: {
          repositorySelector: {repositoryLocationName: 'location', repositoryName: 'repo.py'},
          partitionsDefName: 'fruits',
          partitionKeys: ['apple', 'fig'],
        },
      },
      result: jest.fn(() => ({
        data: buildMutation({
          deleteDynamicPartitions: buildDeleteDynamicPartitionsSuccess(),
        }),
      })),
    };

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
    );

    await waitFor(() => {
      expect(screen.getByText('Delete fruits partitions')).toBeVisible();
    });

    const selectPartition = await screen.findByText('Select a partition');
    await user.click(selectPartition);

    await user.click(await screen.findByTestId('menu-item-apple'));
    await user.click(await screen.findByTestId(`menu-item-fig`));

    await user.click(await screen.findByText(/delete 2 partitions/i));

    expect(deletePartitionsMock.result).toHaveBeenCalled();
  });
});
