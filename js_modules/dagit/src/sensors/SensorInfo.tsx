import {Callout, Intent} from '@blueprintjs/core';
import * as React from 'react';

import {DaemonHealthFragment} from 'src/instance/types/DaemonHealthFragment';

export const SensorInfo: React.FunctionComponent<{
  daemonHealth: DaemonHealthFragment | undefined;
}> = ({daemonHealth}) => {
  let healthy = false;

  if (daemonHealth) {
    const sensorHealths = daemonHealth.allDaemonStatuses.filter(
      (daemon) => daemon.daemonType == 'SENSOR',
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
    <Callout icon="time" intent={Intent.WARNING} title="The sensor daemon is not running.">
      <p>
        See the <a href="https://docs.dagster.io/overview/daemon">dagster-daemon documentation</a>{' '}
        for more information on how to deploy the dagster-daemon process.
      </p>
    </Callout>
  );
};
