import {Resolvers} from '@apollo/client';
import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
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
    await act(async () => {
      render(<Test mocks={[GetScheduleQueryMock, ScheduleDryRunMutationRunRequests]} />);
    });
    await waitFor(async () => {
      const selectButton = screen.getByTestId('tick-selection');
      expect(selectButton).toBeVisible();
      await userEvent.click(selectButton);
    });
    await waitFor(() => {
      expect(screen.getByTestId('tick-5')).toBeVisible();
    });
    await userEvent.click(screen.getByTestId('tick-5'));
    await userEvent.click(screen.getByTestId('evaluate'));
    await waitFor(() => {
      expect(screen.getByText(/1\s+run request/gi)).toBeVisible();
    });
  });

  it('renders errors', async () => {
    await act(async () => {
      render(<Test mocks={[GetScheduleQueryMock, ScheduleDryRunMutationError]} />);
    });
    await waitFor(async () => {
      expect(screen.getByTestId('tick-selection')).toBeVisible();
    });
    await userEvent.click(screen.getByTestId('tick-selection'));
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
    await act(async () => {
      render(<Test mocks={[GetScheduleQueryMock, ScheduleDryRunMutationSkipped]} />);
    });
    await waitFor(async () => {
      const selectButton = screen.getByTestId('tick-selection');
      expect(selectButton).toBeVisible();
      await userEvent.click(selectButton);
    });
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
