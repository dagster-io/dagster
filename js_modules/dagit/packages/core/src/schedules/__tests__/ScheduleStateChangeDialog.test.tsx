import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {ScheduleStateChangeDialog} from '../ScheduleStateChangeDialog';
import {
  buildTurnOffDelawareSuccess,
  buildTurnOffHawaiiError,
  buildTurnOffHawaiiSuccess,
  buildTurnOnAlaskaSuccess,
  buildTurnOnColoradoError,
  buildTurnOnColoradoSuccess,
  scheduleAlaskaCurrentlyOff,
  scheduleColoradoCurrentlyOff,
  scheduleDelawareCurrentlyOn,
  scheduleHawaiiCurrentlyOn,
} from '../__fixtures__/ScheduleState.fixtures';

jest.mock('../..//runs/NavigationBlock', () => ({
  NavigationBlock: () => <div />,
}));

describe('ScheduleStateChangeDialog', () => {
  describe('Initial rendering', () => {
    it('shows content when turning on single schedule', () => {
      render(
        <MockedProvider>
          <ScheduleStateChangeDialog
            openWithIntent="turn-on"
            schedules={[scheduleAlaskaCurrentlyOff]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/1 schedule will be turned on\. do you wish to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /turn on 1 schedule/i})).toBeVisible();
    });

    it('shows content when turning on multiple schedules', () => {
      render(
        <MockedProvider>
          <ScheduleStateChangeDialog
            openWithIntent="turn-on"
            schedules={[scheduleAlaskaCurrentlyOff, scheduleColoradoCurrentlyOff]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/2 schedules will be turned on\. do you wish to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /turn on 2 schedules/i})).toBeVisible();
    });

    it('shows content when turning off single schedule', () => {
      render(
        <MockedProvider>
          <ScheduleStateChangeDialog
            openWithIntent="turn-off"
            schedules={[scheduleDelawareCurrentlyOn]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/1 schedule will be turned off\. do you wish to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /turn off 1 schedule/i})).toBeVisible();
    });

    it('shows content when turning off multiple schedules', () => {
      render(
        <MockedProvider>
          <ScheduleStateChangeDialog
            openWithIntent="turn-off"
            schedules={[scheduleDelawareCurrentlyOn, scheduleHawaiiCurrentlyOn]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/2 schedules will be turned off\. do you wish to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /turn off 2 schedules/i})).toBeVisible();
    });
  });

  describe('Mutation: turn on', () => {
    it('turns on schedules', async () => {
      const mocks = [buildTurnOnAlaskaSuccess(100), buildTurnOnColoradoSuccess(100)];

      render(
        <MockedProvider mocks={mocks}>
          <ScheduleStateChangeDialog
            openWithIntent="turn-on"
            schedules={[scheduleAlaskaCurrentlyOff, scheduleColoradoCurrentlyOff]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      const confirmButton = screen.getByRole('button', {name: /turn on/i});
      userEvent.click(confirmButton);

      await waitFor(() => {
        const button = screen.getByRole('button', {name: /turning on/i});
        expect(button).toBeVisible();
        expect(button).toBeDisabled();
      });

      await waitFor(() => {
        expect(screen.getByText(/successfully turned on 2 schedules/i)).toBeVisible();
      });
    });

    it('shows error when turning on a schedule fails', async () => {
      const mocks = [buildTurnOnAlaskaSuccess(100), buildTurnOnColoradoError(100)];

      render(
        <MockedProvider mocks={mocks}>
          <ScheduleStateChangeDialog
            openWithIntent="turn-on"
            schedules={[scheduleAlaskaCurrentlyOff, scheduleColoradoCurrentlyOff]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      const confirmButton = screen.getByRole('button', {name: /turn on/i});
      userEvent.click(confirmButton);

      await waitFor(() => {
        const button = screen.getByRole('button', {name: /turning on/i});
        expect(button).toBeVisible();
        expect(button).toBeDisabled();
      });

      await waitFor(() => {
        expect(screen.getByText(/successfully turned on 1 schedule/i)).toBeVisible();
      });

      expect(screen.getByText(/could not turn on 1 schedule/i)).toBeVisible();
      const errorItem = screen.getByRole('listitem');

      expect(errorItem.textContent).toMatch(/colorado/i);
      expect(errorItem.textContent).toMatch(/lol u cannot/i);
    });
  });

  describe('Mutation: turn off', () => {
    it('turns off schedules', async () => {
      const mocks = [buildTurnOffDelawareSuccess(100), buildTurnOffHawaiiSuccess(100)];

      render(
        <MockedProvider mocks={mocks}>
          <ScheduleStateChangeDialog
            openWithIntent="turn-off"
            schedules={[scheduleDelawareCurrentlyOn, scheduleHawaiiCurrentlyOn]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      const confirmButton = screen.getByRole('button', {name: /turn off/i});
      userEvent.click(confirmButton);

      await waitFor(() => {
        const button = screen.getByRole('button', {name: /turning off/i});
        expect(button).toBeVisible();
        expect(button).toBeDisabled();
      });

      await waitFor(() => {
        expect(screen.getByText(/successfully turned off 2 schedules/i)).toBeVisible();
      });
    });

    it('shows error when turning off a schedule fails', async () => {
      const mocks = [buildTurnOffDelawareSuccess(100), buildTurnOffHawaiiError(100)];

      render(
        <MockedProvider mocks={mocks}>
          <ScheduleStateChangeDialog
            openWithIntent="turn-off"
            schedules={[scheduleDelawareCurrentlyOn, scheduleHawaiiCurrentlyOn]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      const confirmButton = screen.getByRole('button', {name: /turn off/i});
      userEvent.click(confirmButton);

      await waitFor(() => {
        const button = screen.getByRole('button', {name: /turning off/i});
        expect(button).toBeVisible();
        expect(button).toBeDisabled();
      });

      await waitFor(() => {
        expect(screen.getByText(/successfully turned off 1 schedule/i)).toBeVisible();
      });

      expect(screen.getByText(/could not turn off 1 schedule/i)).toBeVisible();
      const errorItem = screen.getByRole('listitem');

      expect(errorItem.textContent).toMatch(/hawaii/i);
      expect(errorItem.textContent).toMatch(/lol u cannot/i);
    });
  });
});
