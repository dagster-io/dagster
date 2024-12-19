import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter, useHistory} from 'react-router-dom';

import {Resolvers} from '../../apollo-client';
import {useTrackEvent} from '../../app/analytics';
import {SensorDryRunDialog} from '../SensorDryRunDialog';
import * as Mocks from '../__fixtures__/SensorDryRunDialog.fixtures';

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
      <SensorDryRunDialog
        name="test"
        onClose={onCloseMock}
        isOpen={true}
        repoAddress={{
          name: 'testName',
          location: 'testLocation',
        }}
        jobName="testJobName"
        currentCursor="testCursor"
      />
    </MockedProvider>
  );
}

describe('SensorDryRunTest', () => {
  it('submits sensorDryRun mutation with cursor variable and renders successful result and persists cursor', async () => {
    render(<Test mocks={[Mocks.SensorDryRunMutationRunRequests, Mocks.PersistCursorValueMock]} />);
    const cursorInput = await screen.findByTestId('cursor-input');
    await userEvent.type(cursorInput, 'testing123');
    await userEvent.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText(/3\srun requests/g)).toBeVisible();
      expect(screen.queryByText('Skipped')).toBe(null);
      expect(screen.queryByText('Failed')).toBe(null);
    });
  });

  it('renders errors', async () => {
    render(<Test mocks={[Mocks.SensorDryRunMutationError]} />);
    const cursorInput = await screen.findByTestId('cursor-input');
    await userEvent.type(cursorInput, 'testing123');
    await userEvent.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText('Failed')).toBeVisible();
      expect(screen.queryByText('Skipped')).toBe(null);
    });
  });

  it('renders skip reason', async () => {
    render(<Test mocks={[Mocks.SensorDryRunMutationSkipped]} />);
    const cursorInput = await screen.findByTestId('cursor-input');
    await userEvent.type(cursorInput, 'testing123');
    await userEvent.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText('Skipped')).toBeVisible();
    });
  });

  it('allows you to test again', async () => {
    render(<Test mocks={[Mocks.SensorDryRunMutationError]} />);
    const cursorInput = await screen.findByTestId('cursor-input');
    await userEvent.type(cursorInput, 'testing123');
    await userEvent.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText('Failed')).toBeVisible();
      expect(screen.queryByText('Skipped')).toBe(null);
    });
    await userEvent.click(screen.getByTestId('try-again'));
    expect(screen.queryByText('Failed')).toBe(null);
    expect(screen.queryByText('Skipped')).toBe(null);
    expect(screen.getByTestId('cursor-input')).toBeVisible();
  });

  it('launches all runs with well defined job names', async () => {
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
            Mocks.SensorDryRunMutationRunRequests,
            Mocks.PersistCursorValueMock,
            Mocks.SensorLaunchAllMutation,
          ]}
        />
      </MemoryRouter>,
    );
    const cursorInput = await screen.findByTestId('cursor-input');
    await userEvent.type(cursorInput, 'testing123');
    await userEvent.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText(/3\srun requests/g)).toBeVisible();
      expect(screen.queryByText('Skipped')).toBe(null);
      expect(screen.queryByText('Failed')).toBe(null);
    });

    await waitFor(() => {
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
            Mocks.SensorDryRunMutationRunRequestWithUndefinedJobName,
            Mocks.PersistCursorValueMock,
            Mocks.SensorLaunchAllMutation1JobWithUndefinedJobName,
          ]}
        />
      </MemoryRouter>,
    );
    const cursorInput = await screen.findByTestId('cursor-input');
    await userEvent.type(cursorInput, 'testing123');
    await userEvent.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText(/1\srun requests/g)).toBeVisible();
      expect(screen.queryByText('Skipped')).toBe(null);
      expect(screen.queryByText('Failed')).toBe(null);
    });

    await waitFor(() => {
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
