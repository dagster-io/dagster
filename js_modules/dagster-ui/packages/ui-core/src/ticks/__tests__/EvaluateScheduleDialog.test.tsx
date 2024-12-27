import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter, useHistory} from 'react-router-dom';

import {Resolvers} from '../../apollo-client';
import {useTrackEvent} from '../../app/analytics';
import {EvaluateScheduleDialog} from '../EvaluateScheduleDialog';
import {
  GetScheduleQueryMock,
  ScheduleDryRunMutationError,
  ScheduleDryRunMutationRunRequests,
  ScheduleDryRunMutationRunRequestsWithUndefinedName,
  ScheduleDryRunMutationSkipped,
  ScheduleLaunchAllMutation,
  ScheduleLaunchAllMutationWithUndefinedName,
} from '../__fixtures__/EvaluateScheduleDialog.fixtures';

// This component is unit tested separately so mocking it out
jest.mock('../DryRunRequestTable', () => {
  return {
    RunRequestTable: () => <div />,
  };
});

// Mocking useHistory
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useHistory: jest.fn(),
}));

// Mocking useTrackEvent
jest.mock('../../app/analytics', () => ({
  useTrackEvent: jest.fn(() => jest.fn()),
}));

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
    await userEvent.click(screen.getByTestId('continue'));
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
    await waitFor(() => {
      expect(screen.getByTestId('continue')).not.toBeDisabled();
    });
    await userEvent.click(screen.getByTestId('continue'));
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
    await userEvent.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText('Skipped')).toBeVisible();
    });
  });

  it('allows you to test again', async () => {
    render(<Test mocks={[GetScheduleQueryMock, ScheduleDryRunMutationSkipped]} />);
    const selectButton = await screen.findByTestId('tick-selection');
    await userEvent.click(selectButton);
    await waitFor(() => {
      expect(screen.getByTestId('tick-5')).toBeVisible();
    });
    await userEvent.click(screen.getByTestId('tick-5'));
    await userEvent.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText('Skipped')).toBeVisible();
    });
    await userEvent.click(screen.getByTestId('try-again'));
    expect(screen.queryByText('Failed')).toBe(null);
    expect(screen.queryByText('Skipped')).toBe(null);
  });

  it('launches all runs', async () => {
    const pushSpy = jest.fn();
    const createHrefSpy = jest.fn();

    (useHistory as jest.Mock).mockReturnValue({
      push: pushSpy,
      createHref: createHrefSpy,
    });

    (useTrackEvent as jest.Mock).mockReturnValue(jest.fn());

    render(
      <MemoryRouter initialEntries={['/automation']}>
        <Test
          mocks={[
            GetScheduleQueryMock,
            ScheduleDryRunMutationRunRequests,
            ScheduleLaunchAllMutation,
          ]}
        />
      </MemoryRouter>,
    );
    const selectButton = await screen.findByTestId('tick-selection');
    await userEvent.click(selectButton);
    await waitFor(() => {
      expect(screen.getByTestId('tick-5')).toBeVisible();
    });
    await userEvent.click(screen.getByTestId('tick-5'));
    await userEvent.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText(/1\s+run request/i)).toBeVisible();
      expect(screen.getByTestId('launch-all')).not.toBeDisabled();
    });

    userEvent.click(screen.getByTestId('launch-all'));

    await waitFor(() => {
      expect(screen.getByText(/Launching runs/i)).toBeVisible();
    });

    await waitFor(() => {
      expect(pushSpy).toHaveBeenCalled();
    });
  });

  it('launches all runs for 1 runrequest with undefined job name in the runrequest', async () => {
    const pushSpy = jest.fn();
    const createHrefSpy = jest.fn();

    (useHistory as jest.Mock).mockReturnValue({
      push: pushSpy,
      createHref: createHrefSpy,
    });

    (useTrackEvent as jest.Mock).mockReturnValue(jest.fn());

    render(
      <MemoryRouter initialEntries={['/automation']}>
        <Test
          mocks={[
            GetScheduleQueryMock,
            ScheduleDryRunMutationRunRequestsWithUndefinedName,
            ScheduleLaunchAllMutationWithUndefinedName,
          ]}
        />
      </MemoryRouter>,
    );
    const selectButton = await screen.findByTestId('tick-selection');
    await userEvent.click(selectButton);
    await waitFor(() => {
      expect(screen.getByTestId('tick-5')).toBeVisible();
    });
    await userEvent.click(screen.getByTestId('tick-5'));
    await userEvent.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText(/1\s+run request/i)).toBeVisible();
      expect(screen.getByTestId('launch-all')).not.toBeDisabled();
    });

    userEvent.click(screen.getByTestId('launch-all'));

    await waitFor(() => {
      expect(screen.getByText(/Launching runs/i)).toBeVisible();
    });

    await waitFor(() => {
      expect(pushSpy).toHaveBeenCalled();
    });
  });
});
