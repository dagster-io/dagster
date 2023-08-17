import {Resolvers} from '@apollo/client';
import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {EvaluateScheduleDialog} from '../EvaluateScheduleDialog';
import {
  GetScheduleQueryMock,
  ScheduleDryRunMutationError,
  ScheduleDryRunMutationRunRequests,
  ScheduleDryRunMutationSkipped,
} from '../__fixtures__/EvaluateScheduleDialog.fixtures';

// This component is unit tested separately so mocking it out
jest.mock('../DryRunRequestTable', () => {
  return {
    RunRequestTable: () => <div />,
  };
});

const onCloseMock = jest.fn();

function Test({mocks, resolvers}: {mocks?: MockedResponse[]; resolvers?: Resolvers}) {
  return (
    <MockedProvider mocks={mocks} resolvers={resolvers}>
      <EvaluateScheduleDialog
        name="test"
        onClose={onCloseMock}
        isOpen={true}
        repoAddress={{
          name: 'testName',
          location: 'testLocation',
        }}
        jobName="testJobName"
      />
    </MockedProvider>
  );
}

describe('EvaluateScheduleTest', () => {
  it('submits evaluateSchedule mutation with cursor variable and renders successful result and persists cursor', async () => {
    render(<Test mocks={[GetScheduleQueryMock, ScheduleDryRunMutationRunRequests]} />);
    const selectButton = await screen.findByTestId('tick-selection');
    await userEvent.click(selectButton);
    await waitFor(() => {
      expect(screen.getByTestId('tick-5')).toBeVisible();
    });
    await userEvent.click(screen.getByTestId('tick-5'));
    await userEvent.click(screen.getByTestId('evaluate'));
    await waitFor(() => {
      expect(screen.getByText(/1\s+run request/i)).toBeVisible();
    });
  });

  it('renders errors', async () => {
    render(<Test mocks={[GetScheduleQueryMock, ScheduleDryRunMutationError]} />);
    const tickSelection = await screen.findByTestId('tick-selection');
    expect(tickSelection).toBeVisible();
    await userEvent.click(tickSelection);
    await waitFor(() => {
      expect(screen.getByTestId('tick-5')).toBeVisible();
    });
    await userEvent.click(screen.getByTestId('tick-5'));
    await userEvent.click(screen.getByTestId('evaluate'));
    await waitFor(() => {
      expect(screen.getByText('Failed')).toBeVisible();
      expect(screen.queryByText('Skipped')).toBe(null);
    });
  });

  it('renders skip reason', async () => {
    render(<Test mocks={[GetScheduleQueryMock, ScheduleDryRunMutationSkipped]} />);
    const selectButton = await screen.findByTestId('tick-selection');
    await userEvent.click(selectButton);
    await waitFor(() => {
      expect(screen.getByTestId('tick-5')).toBeVisible();
    });
    await userEvent.click(screen.getByTestId('tick-5'));
    await userEvent.click(screen.getByTestId('evaluate'));
    await waitFor(() => {
      expect(screen.getByText('Skipped')).toBeVisible();
    });
  });
});
