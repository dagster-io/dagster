import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import * as CustomAlertProvider from '../../app/CustomAlertProvider';
import {buildUnauthorizedError} from '../../graphql/types';
import {CreatePartitionDialog} from '../CreatePartitionDialog';
import {
  buildCreatePartitionFixture,
  buildCreatePartitionMutation,
} from '../__fixtures__/CreatePartitionDialog.fixture';

let onCloseMock = jest.fn();
let onCreatedMock = jest.fn();

jest.mock('../../app/CustomAlertProvider', () => ({
  CustomAlertProvider: jest.fn(({children}) => children),
  showCustomAlert: jest.fn(),
}));

const showCustomAlertSpy = jest.spyOn(CustomAlertProvider, 'showCustomAlert');

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
        dynamicPartitionsDefinitionName="testPartitionDef"
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
    const user = userEvent.setup();
    const createFixture = buildCreatePartitionFixture({
      partitionsDefName: 'testPartitionDef',
      partitionKey: 'testPartitionName',
    });
    render(<Test mocks={[createFixture]} />);
    const partitionInput = await screen.findByTestId('partition-input');
    await user.type(partitionInput, 'testPartitionName');
    await user.click(screen.getByTestId('save-partition-button'));
    await waitFor(() => {
      expect(onCloseMock).toHaveBeenCalled();
      expect(onCreatedMock).toHaveBeenCalledWith('testPartitionName');
      expect(createFixture.result).toHaveBeenCalled();
    });
  });

  it('Shows error state', async () => {
    const user = userEvent.setup();
    render(<Test mocks={[]} />);
    const partitionInput = await screen.findByTestId('partition-input');
    expect(screen.queryByTestId('warning-icon')).toBeNull();
    await user.type(partitionInput, 'invalidname\n\r\t');
    expect(screen.getByTestId('warning-icon')).toBeVisible();
    await user.clear(partitionInput);
    expect(screen.queryByTestId('warning-icon')).toBeNull();
    await user.type(partitionInput, 'validname');
    expect(screen.queryByTestId('warning-icon')).toBeNull();
  });

  it('Shows error state when mutation fails', async () => {
    const user = userEvent.setup();
    const createFixture = buildCreatePartitionMutation({
      variables: {
        partitionsDefName: 'testPartitionDef',
        partitionKey: 'testPartitionName',
        repositorySelector: {
          repositoryLocationName: 'testing',
          repositoryName: 'testing',
        },
      },
      data: buildUnauthorizedError({
        message: 'test message 123',
      }),
    });
    render(<Test mocks={[createFixture]} />);
    const partitionInput = await screen.findByTestId('partition-input');
    await user.type(partitionInput, 'testPartitionName');
    await user.click(screen.getByTestId('save-partition-button'));
    await waitFor(() => {
      expect(createFixture.result).toHaveBeenCalled();
      expect(showCustomAlertSpy).toHaveBeenCalledWith({
        title: 'Could not add partition',
        body: 'test message 123',
      });
    });
  });
});
