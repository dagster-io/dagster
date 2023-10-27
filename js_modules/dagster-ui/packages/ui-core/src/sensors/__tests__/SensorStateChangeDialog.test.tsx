import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {SensorStateChangeDialog} from '../SensorStateChangeDialog';
import {
  buildStopMinnesotaSuccess,
  buildStopOregonError,
  buildStopOregonSuccess,
  buildStartKansasSuccess,
  buildStartLouisianaError,
  buildStartLouisianaSuccess,
  sensorKansasCurrentlyStopped,
  sensorLouisianaCurrentlyStopped,
  sensorMinnesotaCurrentlyRunning,
  sensorOregonCurrentlyRunning,
} from '../__fixtures__/SensorState.fixtures';

jest.mock('../..//runs/NavigationBlock', () => ({
  NavigationBlock: () => <div />,
}));

describe('SensorStateChangeDialog', () => {
  describe('Initial rendering', () => {
    it('shows content when starting single sensor', () => {
      render(
        <MockedProvider>
          <SensorStateChangeDialog
            openWithIntent="start"
            sensors={[sensorKansasCurrentlyStopped]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/1 sensor will be started\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /start 1 sensor/i})).toBeVisible();
    });

    it('shows content when starting multiple sensors', () => {
      render(
        <MockedProvider>
          <SensorStateChangeDialog
            openWithIntent="start"
            sensors={[sensorKansasCurrentlyStopped, sensorLouisianaCurrentlyStopped]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/2 sensors will be started\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /start 2 sensors/i})).toBeVisible();
    });

    it('shows content when stopping single sensor', () => {
      render(
        <MockedProvider>
          <SensorStateChangeDialog
            openWithIntent="stop"
            sensors={[sensorMinnesotaCurrentlyRunning]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/1 sensor will be stopped\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /stop 1 sensor/i})).toBeVisible();
    });

    it('shows content when stopping multiple sensors', () => {
      render(
        <MockedProvider>
          <SensorStateChangeDialog
            openWithIntent="stop"
            sensors={[sensorMinnesotaCurrentlyRunning, sensorOregonCurrentlyRunning]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/2 sensors will be stopped\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /stop 2 sensors/i})).toBeVisible();
    });
  });

  describe('Mutation: start', () => {
    it('starts sensors', async () => {
      const mocks = [buildStartKansasSuccess(100), buildStartLouisianaSuccess(100)];

      render(
        <MockedProvider mocks={mocks}>
          <SensorStateChangeDialog
            openWithIntent="start"
            sensors={[sensorKansasCurrentlyStopped, sensorLouisianaCurrentlyStopped]}
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
        expect(screen.getByText(/successfully started 2 sensors/i)).toBeVisible();
      });
    });

    it('shows error when starting a sensor fails', async () => {
      const mocks = [buildStartKansasSuccess(100), buildStartLouisianaError(100)];

      render(
        <MockedProvider mocks={mocks}>
          <SensorStateChangeDialog
            openWithIntent="start"
            sensors={[sensorKansasCurrentlyStopped, sensorLouisianaCurrentlyStopped]}
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
        expect(screen.getByText(/successfully started 1 sensor/i)).toBeVisible();
      });

      expect(screen.getByText(/could not start 1 sensor/i)).toBeVisible();
      const errorItem = screen.getByRole('listitem');

      expect(errorItem.textContent).toMatch(/louisiana/i);
      expect(errorItem.textContent).toMatch(/lol u cannot/i);
    });
  });

  describe('Mutation: stop', () => {
    it('stops sensors', async () => {
      const mocks = [buildStopMinnesotaSuccess(100), buildStopOregonSuccess(100)];

      render(
        <MockedProvider mocks={mocks}>
          <SensorStateChangeDialog
            openWithIntent="stop"
            sensors={[sensorMinnesotaCurrentlyRunning, sensorOregonCurrentlyRunning]}
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
        expect(screen.getByText(/successfully stopped 2 sensors/i)).toBeVisible();
      });
    });

    it('shows error when stopping a sensor fails', async () => {
      const mocks = [buildStopMinnesotaSuccess(100), buildStopOregonError(100)];

      render(
        <MockedProvider mocks={mocks}>
          <SensorStateChangeDialog
            openWithIntent="stop"
            sensors={[sensorMinnesotaCurrentlyRunning, sensorOregonCurrentlyRunning]}
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
        expect(screen.getByText(/successfully stopped 1 sensor/i)).toBeVisible();
      });

      expect(screen.getByText(/could not stop 1 sensor/i)).toBeVisible();
      const errorItem = screen.getByRole('listitem');

      expect(errorItem.textContent).toMatch(/oregon/i);
      expect(errorItem.textContent).toMatch(/lol u cannot/i);
    });
  });
});
