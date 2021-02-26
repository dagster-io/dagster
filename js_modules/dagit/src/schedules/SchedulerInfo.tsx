import {gql} from '@apollo/client';
import {Code} from '@blueprintjs/core';
import * as React from 'react';

import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {DaemonHealthFragment} from 'src/instance/types/DaemonHealthFragment';
import {SchedulerFragment} from 'src/schedules/types/SchedulerFragment';
import {Alert} from 'src/ui/Alert';
import {Group} from 'src/ui/Group';
import {FontFamily} from 'src/ui/styles';

export const SCHEDULER_FRAGMENT = gql`
  fragment SchedulerFragment on SchedulerOrError {
    __typename
    ... on SchedulerNotDefinedError {
      message
    }
    ... on Scheduler {
      schedulerClass
    }
    ...PythonErrorFragment
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

export const SchedulerInfo: React.FunctionComponent<{
  errorsOnly?: boolean;
  schedulerOrError: SchedulerFragment;
  daemonHealth: DaemonHealthFragment | undefined;
}> = ({errorsOnly = false, schedulerOrError, daemonHealth}) => {
  if (schedulerOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={schedulerOrError} />;
  }

  if (
    schedulerOrError.__typename === 'Scheduler' &&
    schedulerOrError.schedulerClass == 'DagsterDaemonScheduler'
  ) {
    let healthy = false;

    if (daemonHealth) {
      const schedulerHealths = daemonHealth.allDaemonStatuses.filter(
        (daemon) => daemon.daemonType == 'SCHEDULER',
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
  }

  if (schedulerOrError.__typename === 'SchedulerNotDefinedError') {
    return (
      <Alert
        intent="warning"
        title="The current dagster instance does not have a scheduler configured."
        description={
          <Group direction="column" spacing={12}>
            <div>
              A scheduler must be configured on the instance to run schedules. Therefore, the
              schedules below are not currently running. You can configure a scheduler on the
              instance through the <Code>dagster.yaml</Code> file in <Code>$DAGSTER_HOME</Code>
            </div>
            <div>
              See the{' '}
              <a href="https://docs.dagster.io/overview/instances/dagster-instance#instance-configuration-yaml">
                instance configuration documentation
              </a>{' '}
              for more information.
            </div>
          </Group>
        }
      />
    );
  }

  if (!errorsOnly && schedulerOrError.__typename === 'Scheduler') {
    return (
      <Alert
        intent="info"
        title={
          <div>
            Scheduler class:{' '}
            <span style={{fontFamily: FontFamily.monospace}}>
              {schedulerOrError.schedulerClass}
            </span>
          </div>
        }
      />
    );
  }

  return null;
};
