import * as React from 'react';

import {DaemonHealthFragment} from '../instance/types/DaemonHealthFragment';
import {Alert} from '../ui/Alert';

export const SensorInfo: React.FC<{
  daemonHealth: DaemonHealthFragment | undefined;
}> = ({daemonHealth}) => {
  let healthy = false;

  if (daemonHealth) {
    const sensorHealths = daemonHealth.allDaemonStatuses.filter(
      (daemon) => daemon.daemonType === 'SENSOR',
    );
    if (sensorHealths) {
      const sensorHealth = sensorHealths[0];
      healthy = !!(sensorHealth.required && sensorHealth.healthy);
    }
  }

  if (healthy) {
    return null;
  }

  return (
    <Alert
      intent="warning"
      title="The sensor daemon is not running."
      description={
        <div>
          See the{' '}
          <a
            href="https://docs.dagster.io/deployment/dagster-daemon"
            target="_blank"
            rel="noreferrer"
          >
            dagster-daemon documentation
          </a>{' '}
          for more information on how to deploy the dagster-daemon process.
        </div>
      }
    />
  );
};
