import * as React from 'react';

import {DaemonHealthFragment} from '../instance/types/DaemonHealthFragment';
import {Alert} from '../ui/Alert';

export const SchedulerInfo: React.FunctionComponent<{
  daemonHealth: DaemonHealthFragment | undefined;
}> = ({daemonHealth}) => {
  let healthy = false;

  if (daemonHealth) {
    const schedulerHealths = daemonHealth.allDaemonStatuses.filter(
      (daemon) => daemon.daemonType === 'SCHEDULER',
    );
    if (schedulerHealths) {
      const schedulerHealth = schedulerHealths[0];
      healthy = !!(schedulerHealth.required && schedulerHealth.healthy);
    }
  }

  if (!healthy) {
    return (
      <Alert
        intent="warning"
        title="The scheduler daemon is not running."
        description={
          <div>
            See the{' '}
            <a href="https://docs.dagster.io/overview/daemon">dagster-daemon documentation</a> for
            more information on how to deploy the dagster-daemon process.
          </div>
        }
      />
    );
  }

  return null;
};
