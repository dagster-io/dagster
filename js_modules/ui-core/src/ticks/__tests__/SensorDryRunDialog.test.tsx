import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter, useHistory} from 'react-router-dom';

import {Resolvers} from '../../apollo-client';
import * as CustomAlertProvider from '../../app/CustomAlertProvider';
import {useTrackEvent} from '../../app/analytics';
import {TestPermissionsProvider} from '../../testing/TestPermissions';
import {SensorDryRunDialog} from '../SensorDryRunDialog';
import * as Mocks from '../__fixtures__/SensorDryRunDialog.fixtures';

// Mock run config dialog since it's not relevant to these tests
jest.mock('../../runs/RunConfigDialog', () => {
  return {
    RunConfigDialog: () => <div />,
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

jest.mock('../../app/CustomAlertProvider', () => ({
  CustomAlertProvider: jest.fn(({children}) => children),
  showCustomAlert: jest.fn(),
}));

const onCloseMock = jest.fn();

// Asset-event idempotency keys are randomly generated (crypto.randomUUID()) so a retry
// reuses a stable key even if the client never saw the previous response. Mock them to
// deterministic, sequential values so fixtures can assert on exact mutation variables.
let idempotencyKeyCounter = 0;
beforeEach(() => {
  idempotencyKeyCounter = 0;
  // jsdom's `crypto` has no `randomUUID` to spy on, so define it directly.
  globalThis.crypto.randomUUID = jest.fn(
    () =>
      `idempotency-key-${idempotencyKeyCounter++}` as `${string}-${string}-${string}-${string}-${string}`,
  );
});

function Test({
  mocks,
  resolvers,
  canEditDynamicPartitions = true,
}: {
  mocks?: MockedResponse[];
  resolvers?: Resolvers;
  canEditDynamicPartitions?: boolean;
}) {
  return (
    <MemoryRouter>
      <MockedProvider mocks={mocks} resolvers={resolvers}>
        <TestPermissionsProvider
          locationOverrides={{
            testLocation: {
              canEditDynamicPartitions: {
                enabled: canEditDynamicPartitions,
                disabledReason: canEditDynamicPartitions
                  ? ''
                  : 'You do not have permission to create dynamic partitions.',
              },
            },
          }}
        >
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
        </TestPermissionsProvider>
      </MockedProvider>
    </MemoryRouter>
  );
}

describe('SensorDryRunTest', () => {
  it('submits sensorDryRun mutation with cursor variable and renders successful result and persists cursor', async () => {
    const user = userEvent.setup();
    render(<Test mocks={[Mocks.SensorDryRunMutationRunRequests, Mocks.PersistCursorValueMock]} />);
    const cursorInput = await screen.findByTestId('cursor-input');
    await user.type(cursorInput, 'testing123');
    await user.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText(/3\srun requests/g)).toBeVisible();
      expect(screen.queryByText('Skipped')).toBe(null);
      expect(screen.queryByText('Failed')).toBe(null);
    });
  });

  it('renders errors', async () => {
    const user = userEvent.setup();
    render(<Test mocks={[Mocks.SensorDryRunMutationError]} />);
    const cursorInput = await screen.findByTestId('cursor-input');
    await user.type(cursorInput, 'testing123');
    await user.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText('Failed')).toBeVisible();
      expect(screen.queryByText('Skipped')).toBe(null);
    });
  });

  it('renders skip reason', async () => {
    const user = userEvent.setup();
    render(<Test mocks={[Mocks.SensorDryRunMutationSkipped]} />);
    const cursorInput = await screen.findByTestId('cursor-input');
    await user.type(cursorInput, 'testing123');
    await user.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText('Skipped')).toBeVisible();
    });
  });

  it('allows you to test again', async () => {
    const user = userEvent.setup();
    render(<Test mocks={[Mocks.SensorDryRunMutationError]} />);
    const cursorInput = await screen.findByTestId('cursor-input');
    await user.type(cursorInput, 'testing123');
    await user.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText('Failed')).toBeVisible();
      expect(screen.queryByText('Skipped')).toBe(null);
    });
    await user.click(screen.getByTestId('try-again'));
    expect(screen.queryByText('Failed')).toBe(null);
    expect(screen.queryByText('Skipped')).toBe(null);
    expect(screen.getByTestId('cursor-input')).toBeVisible();
  });

  it('launches all runs with well defined job names', async () => {
    const user = userEvent.setup();
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
    await user.type(cursorInput, 'testing123');
    await user.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText(/3\srun requests/g)).toBeVisible();
      expect(screen.queryByText('Skipped')).toBe(null);
      expect(screen.queryByText('Failed')).toBe(null);
    });

    await waitFor(() => {
      expect(screen.getByTestId('launch-all')).not.toBeDisabled();
    });

    user.click(screen.getByTestId('launch-all'));

    await waitFor(() => {
      expect(screen.getByText(/Launching runs/i)).toBeVisible();
    });

    await waitFor(() => {
      expect(pushSpy).toHaveBeenCalled();
    });
  });

  it('shows apply button for dynamic partition requests with no run requests', async () => {
    const user = userEvent.setup();
    render(<Test mocks={[Mocks.SensorDryRunMutationDynamicPartitionsOnly]} />);
    const cursorInput = await screen.findByTestId('cursor-input');
    await user.type(cursorInput, 'testing123');
    await user.click(screen.getByTestId('continue'));
    // Should show "Apply requests & commit tick result", not just "Commit tick result"
    expect(await screen.findByTestId('launch-all')).toBeVisible();
    expect(screen.queryByTestId('commit-tick-result')).toBe(null);
  });

  it('preflights EDIT_DYNAMIC_PARTITIONS and fires no mutations when the user lacks it', async () => {
    const showCustomAlertSpy = jest.spyOn(CustomAlertProvider, 'showCustomAlert');
    showCustomAlertSpy.mockClear();
    onCloseMock.mockClear();

    (useHistory as jest.Mock).mockReturnValue({push: jest.fn(), createHref: jest.fn()});
    (useTrackEvent as jest.Mock).mockReturnValue(jest.fn());

    const user = userEvent.setup();
    render(
      <Test
        canEditDynamicPartitions={false}
        mocks={[
          Mocks.SensorDryRunMutationWithDynamicPartitionRequest,
          // no partition/launch mocks: an unmatched request fails the test
        ]}
      />,
    );

    const cursorInput = await screen.findByTestId('cursor-input');
    await user.type(cursorInput, 'testing123');
    await user.click(screen.getByTestId('continue'));

    await waitFor(() => {
      expect(screen.getByTestId('launch-all')).not.toBeDisabled();
    });

    await user.click(screen.getByTestId('launch-all'));

    await waitFor(() => {
      expect(showCustomAlertSpy).toHaveBeenCalledWith({
        title: 'Insufficient permissions',
        body: 'You do not have permission to create dynamic partitions.',
      });
    });

    expect(onCloseMock).not.toHaveBeenCalled();
  });

  it('does not launch runs when a mid-flight partition mutation returns UnauthorizedError', async () => {
    const showCustomAlertSpy = jest.spyOn(CustomAlertProvider, 'showCustomAlert');
    showCustomAlertSpy.mockClear();
    onCloseMock.mockClear();

    (useHistory as jest.Mock).mockReturnValue({push: jest.fn(), createHref: jest.fn()});
    (useTrackEvent as jest.Mock).mockReturnValue(jest.fn());

    const user = userEvent.setup();
    render(
      <Test
        canEditDynamicPartitions={true}
        mocks={[
          Mocks.SensorDryRunMutationWithDynamicPartitionRequest,
          Mocks.AddDynamicPartitionUnauthorizedMock,
          // No SensorLaunchAllMutation mock — an unmatched request fails the test.
        ]}
      />,
    );

    const cursorInput = await screen.findByTestId('cursor-input');
    await user.type(cursorInput, 'testing123');
    await user.click(screen.getByTestId('continue'));

    await waitFor(() => {
      expect(screen.getByTestId('launch-all')).not.toBeDisabled();
    });

    await user.click(screen.getByTestId('launch-all'));

    await waitFor(() => {
      expect(showCustomAlertSpy).toHaveBeenCalledWith({
        title: 'Insufficient permissions',
        body: 'You do not have permission to create dynamic partitions.',
      });
    });

    expect(onCloseMock).not.toHaveBeenCalled();
  });

  it('reports asset events and shows "Commit tick result" (not Skipped) when the sensor only returns asset events', async () => {
    const user = userEvent.setup();
    render(
      <Test
        mocks={[
          Mocks.SensorDryRunMutationAssetEventsOnly,
          Mocks.ReportSensorTickAssetEventsMutationMock,
          Mocks.PersistCursorValueMock,
        ]}
      />,
    );
    const cursorInput = await screen.findByTestId('cursor-input');
    await user.type(cursorInput, 'testing123');
    await user.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText(/1\sasset\sevent\b/g)).toBeVisible();
      expect(screen.queryByText('Skipped')).toBe(null);
      // Commit-only button (no run requests / dynamic partitions to apply).
      expect(screen.getByTestId('commit-tick-result')).toBeVisible();
    });

    await user.click(screen.getByTestId('commit-tick-result'));

    // ReportSensorTickAssetEventsMutationMock and PersistCursorValueMock both need to
    // be matched for this to resolve -- an unmatched request fails the test.
    await waitFor(() => {
      expect(onCloseMock).toHaveBeenCalled();
    });
  });

  it('shows an error and does not persist the cursor when reporting asset events fails', async () => {
    const showCustomAlertSpy = jest.spyOn(CustomAlertProvider, 'showCustomAlert');
    showCustomAlertSpy.mockClear();
    onCloseMock.mockClear();

    const user = userEvent.setup();
    render(
      <Test
        mocks={[
          Mocks.SensorDryRunMutationAssetEventsOnly,
          Mocks.ReportSensorTickAssetEventsUnauthorizedMock,
          // No PersistCursorValueMock -- an unmatched request fails the test.
        ]}
      />,
    );
    const cursorInput = await screen.findByTestId('cursor-input');
    await user.type(cursorInput, 'testing123');
    await user.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByTestId('commit-tick-result')).toBeVisible();
    });

    await user.click(screen.getByTestId('commit-tick-result'));

    await waitFor(() => {
      expect(showCustomAlertSpy).toHaveBeenCalledWith({
        title: 'Could not report asset events',
        body: 'You do not have permission to report asset events for this code location.',
      });
    });

    expect(onCloseMock).not.toHaveBeenCalled();
  });

  it('does not close the dialog when asset-event reporting fails after runs already launched', async () => {
    const showCustomAlertSpy = jest.spyOn(CustomAlertProvider, 'showCustomAlert');
    showCustomAlertSpy.mockClear();
    onCloseMock.mockClear();

    (useHistory as jest.Mock).mockReturnValue({push: jest.fn(), createHref: jest.fn()});
    (useTrackEvent as jest.Mock).mockReturnValue(jest.fn());

    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={['/automation']}>
        <Test
          mocks={[
            Mocks.SensorDryRunMutationRunRequestsAndAssetEvents,
            Mocks.SensorLaunchAllMutation,
            Mocks.ReportSensorTickAssetEventsUnauthorizedMock,
            // No PersistCursorValueMock -- the cursor must not be persisted after a
            // failed asset-event report, so an unmatched request would fail the test.
          ]}
        />
      </MemoryRouter>,
    );
    const cursorInput = await screen.findByTestId('cursor-input');
    await user.type(cursorInput, 'testing123');
    await user.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByTestId('launch-all')).not.toBeDisabled();
    });

    await user.click(screen.getByTestId('launch-all'));

    await waitFor(() => {
      expect(showCustomAlertSpy).toHaveBeenCalledWith({
        title: 'Could not report asset events',
        body: 'You do not have permission to report asset events for this code location.',
      });
    });

    expect(onCloseMock).not.toHaveBeenCalled();
  });

  it('retries only the remaining asset events after a partial failure', async () => {
    const showCustomAlertSpy = jest.spyOn(CustomAlertProvider, 'showCustomAlert');
    showCustomAlertSpy.mockClear();
    onCloseMock.mockClear();

    const user = userEvent.setup();
    render(
      <Test
        mocks={[
          Mocks.SensorDryRunMutationTwoAssetEvents,
          Mocks.ReportSensorTickAssetEventsPartialFailureMock,
          Mocks.ReportSensorTickAssetEventsRetryRemainderMock,
          Mocks.PersistCursorValueMock,
        ]}
      />,
    );
    const cursorInput = await screen.findByTestId('cursor-input');
    await user.type(cursorInput, 'testing123');
    await user.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByTestId('commit-tick-result')).toBeVisible();
    });

    await user.click(screen.getByTestId('commit-tick-result'));

    await waitFor(() => {
      expect(showCustomAlertSpy).toHaveBeenCalledWith(
        expect.objectContaining({title: 'Could not report all asset events'}),
      );
    });
    expect(onCloseMock).not.toHaveBeenCalled();

    // Retry -- ReportSensorTickAssetEventsRetryRemainderMock only matches a request for
    // the single remaining event; resending both (the original request) would leave this
    // mutation unmatched and fail the test.
    await user.click(screen.getByTestId('commit-tick-result'));

    await waitFor(() => {
      expect(onCloseMock).toHaveBeenCalled();
    });
  });

  it('launches all runs for 1 runrequest with undefined job name in the runrequest', async () => {
    const user = userEvent.setup();
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
    await user.type(cursorInput, 'testing123');
    await user.click(screen.getByTestId('continue'));
    await waitFor(() => {
      expect(screen.getByText(/1\srun request\b/g)).toBeVisible();
      expect(screen.queryByText('Skipped')).toBe(null);
      expect(screen.queryByText('Failed')).toBe(null);
    });

    await waitFor(() => {
      expect(screen.getByTestId('launch-all')).not.toBeDisabled();
    });

    user.click(screen.getByTestId('launch-all'));

    await waitFor(() => {
      expect(screen.getByText(/Launching runs/i)).toBeVisible();
    });

    await waitFor(() => {
      expect(pushSpy).toHaveBeenCalled();
    });
  });
});
