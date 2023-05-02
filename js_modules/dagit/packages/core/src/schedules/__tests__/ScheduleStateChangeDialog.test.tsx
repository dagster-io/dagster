import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {ScheduleStateChangeDialog} from '../ScheduleStateChangeDialog';
import {
  buildStopDelawareSuccess,
  buildStopHawaiiError,
  buildStopHawaiiSuccess,
  buildStartAlaskaSuccess,
  buildStartColoradoError,
  buildStartColoradoSuccess,
  scheduleAlaskaCurrentlyStopped,
  scheduleColoradoCurrentlyStopped,
  scheduleDelawareCurrentlyRunning,
  scheduleHawaiiCurrentlyRunning,
} from '../__fixtures__/ScheduleState.fixtures';

jest.mock('../..//runs/NavigationBlock', () => ({
  NavigationBlock: () => <div />,
}));

describe('ScheduleStateChangeDialog', () => {
  describe('Initial rendering', () => {
    it('shows content when starting single schedule', () => {
      render(
        <MockedProvider>
          <ScheduleStateChangeDialog
            openWithIntent="start"
            schedules={[scheduleAlaskaCurrentlyStopped]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/1 schedule will be started\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /start 1 schedule/i})).toBeVisible();
    });

    it('shows content when starting multiple schedules', () => {
      render(
        <MockedProvider>
          <ScheduleStateChangeDialog
            openWithIntent="start"
            schedules={[scheduleAlaskaCurrentlyStopped, scheduleColoradoCurrentlyStopped]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/2 schedules will be started\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /start 2 schedules/i})).toBeVisible();
    });

    it('shows content when stopping single schedule', () => {
      render(
        <MockedProvider>
          <ScheduleStateChangeDialog
            openWithIntent="stop"
            schedules={[scheduleDelawareCurrentlyRunning]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/1 schedule will be stopped\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /stop 1 schedule/i})).toBeVisible();
    });

    it('shows content when stopping multiple schedules', () => {
      render(
        <MockedProvider>
          <ScheduleStateChangeDialog
            openWithIntent="stop"
            schedules={[scheduleDelawareCurrentlyRunning, scheduleHawaiiCurrentlyRunning]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/2 schedules will be stopped\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /stop 2 schedules/i})).toBeVisible();
    });
  });

  describe('Mutation: start', () => {
    it('starts schedules', async () => {
      const mocks = [buildStartAlaskaSuccess(100), buildStartColoradoSuccess(100)];

      render(
        <MockedProvider mocks={mocks}>
          <ScheduleStateChangeDialog
            openWithIntent="start"
            schedules={[scheduleAlaskaCurrentlyStopped, scheduleColoradoCurrentlyStopped]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      const confirmButton = screen.getByRole('button', {name: /start/i});
      await userEvent.click(confirmButton);

      await waitFor(() => {
        const button = screen.getByRole('button', {name: /starting/i});
        expect(button).toBeVisible();
        expect(button).toBeDisabled();
      });

      await waitFor(() => {
        expect(screen.getByText(/successfully started 2 schedules/i)).toBeVisible();
      });
    });

    it('shows error when starting a schedule fails', async () => {
      const mocks = [buildStartAlaskaSuccess(100), buildStartColoradoError(100)];

      render(
        <MockedProvider mocks={mocks}>
          <ScheduleStateChangeDialog
            openWithIntent="start"
            schedules={[scheduleAlaskaCurrentlyStopped, scheduleColoradoCurrentlyStopped]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      const confirmButton = screen.getByRole('button', {name: /start/i});
      await userEvent.click(confirmButton);

      await waitFor(() => {
        const button = screen.getByRole('button', {name: /starting/i});
        expect(button).toBeVisible();
        expect(button).toBeDisabled();
      });

      await waitFor(() => {
        expect(screen.getByText(/successfully started 1 schedule/i)).toBeVisible();
      });

      expect(screen.getByText(/could not start 1 schedule/i)).toBeVisible();
      const errorItem = screen.getByRole('listitem');

      expect(errorItem.textContent).toMatch(/colorado/i);
      expect(errorItem.textContent).toMatch(/lol u cannot/i);
    });
  });

  describe('Mutation: stop', () => {
    it('stops schedules', async () => {
      const mocks = [buildStopDelawareSuccess(100), buildStopHawaiiSuccess(100)];

      render(
        <MockedProvider mocks={mocks}>
          <ScheduleStateChangeDialog
            openWithIntent="stop"
            schedules={[scheduleDelawareCurrentlyRunning, scheduleHawaiiCurrentlyRunning]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      const confirmButton = screen.getByRole('button', {name: /stop/i});
      await userEvent.click(confirmButton);

      await waitFor(() => {
        const button = screen.getByRole('button', {name: /stopping/i});
        expect(button).toBeVisible();
        expect(button).toBeDisabled();
      });

      await waitFor(() => {
        expect(screen.getByText(/successfully stopped 2 schedules/i)).toBeVisible();
      });
    });

    it('shows error when stopping a schedule fails', async () => {
      const mocks = [buildStopDelawareSuccess(100), buildStopHawaiiError(100)];

      render(
        <MockedProvider mocks={mocks}>
          <ScheduleStateChangeDialog
            openWithIntent="stop"
            schedules={[scheduleDelawareCurrentlyRunning, scheduleHawaiiCurrentlyRunning]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      const confirmButton = screen.getByRole('button', {name: /stop/i});
      await userEvent.click(confirmButton);

      await waitFor(() => {
        const button = screen.getByRole('button', {name: /stopping/i});
        expect(button).toBeVisible();
        expect(button).toBeDisabled();
      });

      await waitFor(() => {
        expect(screen.getByText(/successfully stopped 1 schedule/i)).toBeVisible();
      });

      expect(screen.getByText(/could not stop 1 schedule/i)).toBeVisible();
      const errorItem = screen.getByRole('listitem');

      expect(errorItem.textContent).toMatch(/hawaii/i);
      expect(errorItem.textContent).toMatch(/lol u cannot/i);
    });
  });
});
