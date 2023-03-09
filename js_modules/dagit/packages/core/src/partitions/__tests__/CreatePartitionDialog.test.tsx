import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {CreatePartitionDialog} from '../CreatePartitionDialog';
import {buildCreatePartitionFixture} from '../__fixtures__/CreatePartitionDialog.fixture';

let onCloseMock = jest.fn();
let onCreatedMock = jest.fn();

function Test({mocks}: {mocks?: MockedResponse[]}) {
  return (
    <MockedProvider mocks={mocks}>
      <CreatePartitionDialog
        isOpen={true}
        close={onCloseMock}
        repoAddress={{
          name: 'testing',
          location: 'testing',
        }}
        partitionDefinitionName="testPartitionDef"
        onCreated={onCreatedMock}
      />
    </MockedProvider>
  );
}

describe('CreatePartitionDialog', () => {
  beforeEach(() => {
    onCloseMock = jest.fn();
    onCreatedMock = jest.fn();
  });

  it('Submits mutation with correct variables and calls setSelected and onClose', async () => {
    const createFixture = buildCreatePartitionFixture({
      partitionsDefName: 'testPartitionDef',
      partitionKey: 'testPartitionName',
    });
    await act(async () => {
      render(<Test mocks={[createFixture]} />);
    });
    const partitionInput = screen.getByTestId('partition-input');
    userEvent.type(partitionInput, 'testPartitionName');
    userEvent.click(screen.getByTestId('save-partition-button'));
    await waitFor(() => {
      expect(onCloseMock).toHaveBeenCalled();
      expect(onCreatedMock).toHaveBeenCalledWith('testPartitionName');
      expect(createFixture.result).toHaveBeenCalled();
    });
  });

  it('Shows error state', async () => {
    await act(async () => {
      render(<Test mocks={[]} />);
    });
    const partitionInput = screen.getByTestId('partition-input');
    expect(screen.queryByTestId('warning-icon')).toBeNull();
    userEvent.type(partitionInput, 'invalidname\n\r\t');
    expect(screen.getByTestId('warning-icon')).toBeVisible();
    userEvent.clear(partitionInput);
    expect(screen.queryByTestId('warning-icon')).toBeNull();
    userEvent.type(partitionInput, 'validname');
    expect(screen.queryByTestId('warning-icon')).toBeNull();
  });
});
