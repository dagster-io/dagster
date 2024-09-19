import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {AutomationStateChangeDialog} from '../AutomationStateChangeDialog';
import {
  buildStartAlaskaSuccess,
  buildStartColoradoError,
  buildStartColoradoSuccess,
  buildStartKansasSuccess,
  buildStartLouisianaError,
  buildStartLouisianaSuccess,
  buildStopDelawareSuccess,
  buildStopHawaiiError,
  buildStopHawaiiSuccess,
  buildStopMinnesotaSuccess,
  buildStopOregonError,
  buildStopOregonSuccess,
  scheduleAlaskaCurrentlyStopped,
  scheduleColoradoCurrentlyStopped,
  scheduleDelawareCurrentlyRunning,
  scheduleHawaiiCurrentlyRunning,
  sensorKansasCurrentlyStopped,
  sensorLouisianaCurrentlyStopped,
  sensorMinnesotaCurrentlyRunning,
  sensorOregonCurrentlyRunning,
} from '../__fixtures__/AutomationState.fixtures';

jest.mock('../../runs/NavigationBlock', () => ({
  NavigationBlock: () => <div />,
}));

describe('AutomationStateChangeDialog', () => {
  describe('Initial rendering', () => {
    it('shows content when starting single sensor', () => {
      render(
        <MockedProvider>
          <AutomationStateChangeDialog
            openWithIntent="start"
            automations={[sensorKansasCurrentlyStopped]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/1 automation will be started\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /start 1 automation/i})).toBeVisible();
    });

    it('shows content when starting single schedule', () => {
      render(
        <MockedProvider>
          <AutomationStateChangeDialog
            openWithIntent="start"
            automations={[scheduleAlaskaCurrentlyStopped]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/1 automation will be started\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /start 1 automation/i})).toBeVisible();
    });

    it('shows content when starting multiple sensors', () => {
      render(
        <MockedProvider>
          <AutomationStateChangeDialog
            openWithIntent="start"
            automations={[sensorKansasCurrentlyStopped, sensorLouisianaCurrentlyStopped]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/2 automations will be started\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /start 2 automations/i})).toBeVisible();
    });

    it('shows content when starting multiple schedules', () => {
      render(
        <MockedProvider>
          <AutomationStateChangeDialog
            openWithIntent="start"
            automations={[scheduleAlaskaCurrentlyStopped, scheduleColoradoCurrentlyStopped]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/2 automations will be started\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /start 2 automations/i})).toBeVisible();
    });

    it('shows content when starting combination of automations', () => {
      render(
        <MockedProvider>
          <AutomationStateChangeDialog
            openWithIntent="start"
            automations={[
              sensorKansasCurrentlyStopped,
              sensorLouisianaCurrentlyStopped,
              scheduleAlaskaCurrentlyStopped,
              scheduleColoradoCurrentlyStopped,
            ]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/4 automations will be started\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /start 4 automations/i})).toBeVisible();
    });

    it('shows content when stopping single sensor', () => {
      render(
        <MockedProvider>
          <AutomationStateChangeDialog
            openWithIntent="stop"
            automations={[sensorMinnesotaCurrentlyRunning]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/1 automation will be stopped\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /stop 1 automation/i})).toBeVisible();
    });

    it('shows content when stopping multiple sensors', () => {
      render(
        <MockedProvider>
          <AutomationStateChangeDialog
            openWithIntent="stop"
            automations={[sensorMinnesotaCurrentlyRunning, sensorOregonCurrentlyRunning]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/2 automations will be stopped\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /stop 2 automations/i})).toBeVisible();
    });

    it('shows content when stopping single schedule', () => {
      render(
        <MockedProvider>
          <AutomationStateChangeDialog
            openWithIntent="stop"
            automations={[scheduleHawaiiCurrentlyRunning]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/1 automation will be stopped\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /stop 1 automation/i})).toBeVisible();
    });

    it('shows content when stopping multiple schedules', () => {
      render(
        <MockedProvider>
          <AutomationStateChangeDialog
            openWithIntent="stop"
            automations={[scheduleHawaiiCurrentlyRunning, scheduleDelawareCurrentlyRunning]}
            onClose={jest.fn()}
            onComplete={jest.fn()}
          />
        </MockedProvider>,
      );

      expect(
        screen.getByText(/2 automations will be stopped\. do you want to continue\?/i),
      ).toBeVisible();

      expect(screen.getByRole('button', {name: /stop 2 automations/i})).toBeVisible();
    });
  });

  describe('Mutation: start', () => {
    it('starts sensors', async () => {
      const mocks = [buildStartKansasSuccess(100), buildStartLouisianaSuccess(100)];

      render(
        <MockedProvider mocks={mocks}>
          <AutomationStateChangeDialog
            openWithIntent="start"
            automations={[sensorKansasCurrentlyStopped, sensorLouisianaCurrentlyStopped]}
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
        expect(screen.getByText(/successfully started 2 automations/i)).toBeVisible();
      });
    });

    it('shows error when starting a sensor fails', async () => {
      const mocks = [buildStartKansasSuccess(100), buildStartLouisianaError(100)];

      render(
        <MockedProvider mocks={mocks}>
          <AutomationStateChangeDialog
            openWithIntent="start"
            automations={[sensorKansasCurrentlyStopped, sensorLouisianaCurrentlyStopped]}
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
        expect(screen.getByText(/successfully started 1 automation/i)).toBeVisible();
      });

      expect(screen.getByText(/could not start 1 automation/i)).toBeVisible();
      const errorItem = screen.getByRole('listitem');

      expect(errorItem.textContent).toMatch(/louisiana/i);
      expect(errorItem.textContent).toMatch(/lol u cannot/i);
    });

    it('starts schedules', async () => {
      const mocks = [buildStartColoradoSuccess(100), buildStartAlaskaSuccess(100)];

      render(
        <MockedProvider mocks={mocks}>
          <AutomationStateChangeDialog
            openWithIntent="start"
            automations={[scheduleAlaskaCurrentlyStopped, scheduleColoradoCurrentlyStopped]}
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
        expect(screen.getByText(/successfully started 2 automations/i)).toBeVisible();
      });
    });

    it('shows error when starting a schedule fails', async () => {
      const mocks = [buildStartAlaskaSuccess(100), buildStartColoradoError(100)];

      render(
        <MockedProvider mocks={mocks}>
          <AutomationStateChangeDialog
            openWithIntent="start"
            automations={[scheduleAlaskaCurrentlyStopped, scheduleColoradoCurrentlyStopped]}
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
        expect(screen.getByText(/successfully started 1 automation/i)).toBeVisible();
      });

      expect(screen.getByText(/could not start 1 automation/i)).toBeVisible();
      const errorItem = screen.getByRole('listitem');

      expect(errorItem.textContent).toMatch(/colorado/i);
      expect(errorItem.textContent).toMatch(/lol u cannot/i);
    });

    it('starts a combination of schedules and sensors', async () => {
      const mocks = [
        buildStartKansasSuccess(100),
        buildStartLouisianaSuccess(100),
        buildStartColoradoSuccess(100),
        buildStartAlaskaSuccess(100),
      ];

      render(
        <MockedProvider mocks={mocks}>
          <AutomationStateChangeDialog
            openWithIntent="start"
            automations={[
              sensorKansasCurrentlyStopped,
              sensorLouisianaCurrentlyStopped,
              scheduleAlaskaCurrentlyStopped,
              scheduleColoradoCurrentlyStopped,
            ]}
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
        expect(screen.getByText(/successfully started 4 automations/i)).toBeVisible();
      });
    });

    it('shows errors when starting a combination of schedules and sensors', async () => {
      const mocks = [
        buildStartKansasSuccess(100),
        buildStartLouisianaError(100),
        buildStartColoradoError(100),
        buildStartAlaskaSuccess(100),
      ];

      render(
        <MockedProvider mocks={mocks}>
          <AutomationStateChangeDialog
            openWithIntent="start"
            automations={[
              sensorKansasCurrentlyStopped,
              sensorLouisianaCurrentlyStopped,
              scheduleAlaskaCurrentlyStopped,
              scheduleColoradoCurrentlyStopped,
            ]}
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
        expect(screen.getByText(/successfully started 2 automations/i)).toBeVisible();
      });

      expect(screen.getByText(/could not start 2 automations/i)).toBeVisible();
      const errorItems = screen.getAllByRole('listitem');

      expect(errorItems[0]!.textContent).toMatch(/louisiana/i);
      expect(errorItems[0]!.textContent).toMatch(/lol u cannot/i);
      expect(errorItems[1]!.textContent).toMatch(/colorado/i);
      expect(errorItems[1]!.textContent).toMatch(/lol u cannot/i);
    });
  });

  describe('Mutation: stop', () => {
    it('stops sensors', async () => {
      const mocks = [buildStopMinnesotaSuccess(100), buildStopOregonSuccess(100)];

      render(
        <MockedProvider mocks={mocks}>
          <AutomationStateChangeDialog
            openWithIntent="stop"
            automations={[sensorMinnesotaCurrentlyRunning, sensorOregonCurrentlyRunning]}
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
        expect(screen.getByText(/successfully stopped 2 automations/i)).toBeVisible();
      });
    });

    it('shows error when stopping a sensor fails', async () => {
      const mocks = [buildStopMinnesotaSuccess(100), buildStopOregonError(100)];

      render(
        <MockedProvider mocks={mocks}>
          <AutomationStateChangeDialog
            openWithIntent="stop"
            automations={[sensorMinnesotaCurrentlyRunning, sensorOregonCurrentlyRunning]}
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
        expect(screen.getByText(/successfully stopped 1 automation/i)).toBeVisible();
      });

      expect(screen.getByText(/could not stop 1 automation/i)).toBeVisible();
      const errorItem = screen.getByRole('listitem');

      expect(errorItem.textContent).toMatch(/oregon/i);
      expect(errorItem.textContent).toMatch(/lol u cannot/i);
    });

    it('stops schedules', async () => {
      const mocks = [buildStopDelawareSuccess(100), buildStopHawaiiSuccess(100)];

      render(
        <MockedProvider mocks={mocks}>
          <AutomationStateChangeDialog
            openWithIntent="stop"
            automations={[scheduleDelawareCurrentlyRunning, scheduleHawaiiCurrentlyRunning]}
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
        expect(screen.getByText(/successfully stopped 2 automations/i)).toBeVisible();
      });
    });

    it('shows error when stopping a schedule fails', async () => {
      const mocks = [buildStopDelawareSuccess(100), buildStopHawaiiError(100)];

      render(
        <MockedProvider mocks={mocks}>
          <AutomationStateChangeDialog
            openWithIntent="stop"
            automations={[scheduleDelawareCurrentlyRunning, scheduleHawaiiCurrentlyRunning]}
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
        expect(screen.getByText(/successfully stopped 1 automation/i)).toBeVisible();
      });

      expect(screen.getByText(/could not stop 1 automation/i)).toBeVisible();
      const errorItem = screen.getByRole('listitem');

      expect(errorItem.textContent).toMatch(/hawaii/i);
      expect(errorItem.textContent).toMatch(/lol u cannot/i);
    });

    it('stops a combination of sensors and schedules', async () => {
      const mocks = [
        buildStopMinnesotaSuccess(100),
        buildStopOregonSuccess(100),
        buildStopDelawareSuccess(100),
        buildStopHawaiiSuccess(100),
      ];

      render(
        <MockedProvider mocks={mocks}>
          <AutomationStateChangeDialog
            openWithIntent="stop"
            automations={[
              sensorMinnesotaCurrentlyRunning,
              sensorOregonCurrentlyRunning,
              scheduleDelawareCurrentlyRunning,
              scheduleHawaiiCurrentlyRunning,
            ]}
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
        expect(screen.getByText(/successfully stopped 4 automations/i)).toBeVisible();
      });
    });

    it('shows errors when stopping a combination of schedules and sensors', async () => {
      const mocks = [
        buildStopMinnesotaSuccess(100),
        buildStopOregonError(100),
        buildStopDelawareSuccess(100),
        buildStopHawaiiError(100),
      ];

      render(
        <MockedProvider mocks={mocks}>
          <AutomationStateChangeDialog
            openWithIntent="stop"
            automations={[
              sensorMinnesotaCurrentlyRunning,
              sensorOregonCurrentlyRunning,
              scheduleDelawareCurrentlyRunning,
              scheduleHawaiiCurrentlyRunning,
            ]}
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
        expect(screen.getByText(/successfully stopped 2 automations/i)).toBeVisible();
      });

      expect(screen.getByText(/could not stop 2 automations/i)).toBeVisible();
      const errorItems = screen.getAllByRole('listitem');

      expect(errorItems[0]!.textContent).toMatch(/oregon/i);
      expect(errorItems[0]!.textContent).toMatch(/lol u cannot/i);
      expect(errorItems[1]!.textContent).toMatch(/hawaii/i);
      expect(errorItems[1]!.textContent).toMatch(/lol u cannot/i);
    });
  });
});
