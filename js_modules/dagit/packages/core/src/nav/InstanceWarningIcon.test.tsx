import {waitFor} from '@testing-library/dom';
import {render, screen} from '@testing-library/react';
import * as React from 'react';

import {DeploymentStatusProvider, DeploymentStatusType} from '../instance/DeploymentStatusProvider';
import {TestProvider} from '../testing/TestProvider';

import {InstanceWarningIcon} from './InstanceWarningIcon';

describe('InstanceWarningIcon', () => {
  const Test: React.FC<{mocks: any}> = ({mocks}) => {
    return (
      <TestProvider apolloProps={{mocks}}>
        <DeploymentStatusProvider include={new Set<DeploymentStatusType>(['daemons'])}>
          <InstanceWarningIcon />
        </DeploymentStatusProvider>
      </TestProvider>
    );
  };

  it('displays if there are daemon errors', async () => {
    const mocks = {
      DaemonStatus: () => ({
        healthy: () => false,
        required: () => true,
      }),
    };

    render(<Test mocks={[mocks]} />);
    await waitFor(() => {
      expect(screen.queryByLabelText('warning')).toBeVisible();
    });
  });

  it('does not display if no errors', async () => {
    const mocks = {
      DaemonStatus: () => ({
        healthy: () => true,
        required: () => true,
      }),
    };

    render(<Test mocks={[mocks]} />);
    await waitFor(() => {
      expect(screen.queryByLabelText('warning')).toBeNull();
    });
  });

  describe('Schedule/sensor errors', () => {
    describe('Schedule error', () => {
      const daemonStoppedSchedulerMocks = {
        DaemonHealth: () => ({
          allDaemonStatuses: () => [
            {daemonType: 'SCHEDULER', healthy: false, required: true},
            {daemonType: 'SENSOR', healthy: true, required: true},
            {daemonType: 'OTHER', healthy: true, required: true},
          ],
        }),
      };

      it('does not display if there are no schedules, and only a scheduler error', async () => {
        const repoMocks = {
          Repository: () => ({
            sensors: () => [],
            schedules: () => [],
          }),
        };

        render(<Test mocks={[daemonStoppedSchedulerMocks, repoMocks]} />);
        await waitFor(() => {
          expect(screen.queryByLabelText('warning')).toBeNull();
        });
      });

      it('does not display if schedules are not enabled, and only a scheduler error', async () => {
        const repoMocks = {
          Repository: () => ({
            sensors: () => [],
            schedules: () => [{scheduleState: {status: 'STOPPED'}}],
          }),
        };

        render(<Test mocks={[daemonStoppedSchedulerMocks, repoMocks]} />);
        await waitFor(() => {
          expect(screen.queryByLabelText('warning')).toBeNull();
        });
      });

      it('displays if there are running schedules, and only a scheduler error', async () => {
        const repoMocks = {
          Repository: () => ({
            sensors: () => [],
            schedules: () => [{scheduleState: {status: 'RUNNING'}}],
          }),
        };

        render(<Test mocks={[daemonStoppedSchedulerMocks, repoMocks]} />);
        await waitFor(() => {
          expect(screen.queryByLabelText('warning')).toBeVisible();
        });
      });
    });

    describe('Sensor error', () => {
      const daemonStoppedSensorMocks = {
        DaemonHealth: () => ({
          allDaemonStatuses: () => [
            {daemonType: 'SCHEDULER', healthy: true, required: true},
            {daemonType: 'SENSOR', healthy: false, required: true},
            {daemonType: 'OTHER', healthy: true, required: true},
          ],
        }),
      };

      it('does not display if there are no sensors, and only a sensor error', async () => {
        const repoMocks = {
          Repository: () => ({
            sensors: () => [],
            schedules: () => [],
          }),
        };

        render(<Test mocks={[daemonStoppedSensorMocks, repoMocks]} />);
        await waitFor(() => {
          expect(screen.queryByLabelText('warning')).toBeNull();
        });
      });

      it('displays if there are sensors, and only a sensor error', async () => {
        const repoMocks = {
          Repository: () => ({
            sensors: () => [{sensorState: {status: 'RUNNING'}}],
            schedules: () => [],
          }),
        };

        render(<Test mocks={[daemonStoppedSensorMocks, repoMocks]} />);
        await waitFor(() => {
          expect(screen.queryByLabelText('warning')).toBeVisible();
        });
      });
    });

    describe('Schedule and Sensor error', () => {
      const daemonStoppedBothMocks = {
        DaemonHealth: () => ({
          allDaemonStatuses: () => [
            {daemonType: 'SCHEDULER', healthy: false, required: true},
            {daemonType: 'SENSOR', healthy: false, required: true},
            {daemonType: 'OTHER', healthy: true, required: true},
          ],
        }),
      };

      it('does not display if there are no sensors/schedules, and only (both) sensor/schedule errors', async () => {
        const repoMocks = {
          Repository: () => ({
            sensors: () => [],
            schedules: () => [],
          }),
        };

        render(<Test mocks={[daemonStoppedBothMocks, repoMocks]} />);
        await waitFor(() => {
          expect(screen.queryByLabelText('warning')).toBeNull();
        });
      });

      it('displays if there are sensors, and only (both) sensor/schedule errors', async () => {
        const repoMocks = {
          Repository: () => ({
            sensors: () => [{sensorState: {status: 'RUNNING'}}],
            schedules: () => [],
          }),
        };

        render(<Test mocks={[daemonStoppedBothMocks, repoMocks]} />);
        await waitFor(() => {
          expect(screen.queryByLabelText('warning')).toBeVisible();
        });
      });

      it('displays if there are schedules, and only (both) sensor/schedule errors', async () => {
        const repoMocks = {
          Repository: () => ({
            sensors: () => [],
            schedules: () => [{scheduleState: {status: 'RUNNING'}}],
          }),
        };

        render(<Test mocks={[daemonStoppedBothMocks, repoMocks]} />);
        await waitFor(() => {
          expect(screen.queryByLabelText('warning')).toBeVisible();
        });
      });

      it('displays if there are schedules and sensors, and only (both) sensor/schedule errors', async () => {
        const repoMocks = {
          Repository: () => ({
            sensors: () => [{sensorState: {status: 'RUNNING'}}],
            schedules: () => [{scheduleState: {status: 'RUNNING'}}],
          }),
        };

        render(<Test mocks={[daemonStoppedBothMocks, repoMocks]} />);
        await waitFor(() => {
          expect(screen.queryByLabelText('warning')).toBeVisible();
        });
      });
    });

    describe('Other error', () => {
      const daemonStoppedOtherMocks = {
        DaemonHealth: () => ({
          allDaemonStatuses: () => [
            {daemonType: 'SCHEDULER', healthy: true, required: true},
            {daemonType: 'SENSOR', healthy: true, required: true},
            {daemonType: 'OTHER', healthy: false, required: true},
          ],
        }),
      };

      it('displays even if there are no sensors or schedules', async () => {
        const repoMocks = {
          Repository: () => ({
            sensors: () => [],
            schedules: () => [],
          }),
        };

        render(<Test mocks={[daemonStoppedOtherMocks, repoMocks]} />);
        await waitFor(() => {
          expect(screen.queryByLabelText('warning')).toBeNull();
        });
      });
    });
  });
});
