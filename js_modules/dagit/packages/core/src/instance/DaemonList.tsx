import {gql} from '@apollo/client';
import moment from 'moment-timezone';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {Timestamp} from '../app/time/Timestamp';
import {Group} from '../ui/Group';
import {Table} from '../ui/Table';

import {DaemonHealth} from './DaemonHealth';
import {
  DaemonHealthFragment,
  DaemonHealthFragment_allDaemonStatuses as DaemonStatus,
} from './types/DaemonHealthFragment';

interface DaemonLabelProps {
  daemon: DaemonStatus;
}

const DaemonLabel = (props: DaemonLabelProps) => {
  const {daemon} = props;
  switch (daemon.daemonType) {
    case 'SCHEDULER':
      return <div>Scheduler</div>;
    case 'SENSOR':
      return <div>Sensors</div>;
    case 'QUEUED_RUN_COORDINATOR':
      return <div>Run queue</div>;
    case 'BACKFILL':
      return <div>Backfill</div>;
    default:
      return (
        <div style={{textTransform: 'capitalize'}}>
          {daemon.daemonType.replace(/_/g, ' ').toLowerCase()}
        </div>
      );
  }
};

interface Props {
  daemonHealth: DaemonHealthFragment | undefined;
}

const TIME_FORMAT = {showSeconds: true, showTimezone: true};

export const DaemonList = (props: Props) => {
  const {daemonHealth} = props;

  if (!daemonHealth) {
    return null;
  }

  return (
    <Table>
      <thead>
        <tr>
          <th style={{width: '25%'}}>Daemon</th>
          <th style={{width: '30%'}}>Status</th>
          <th>Last heartbeat</th>
        </tr>
      </thead>
      <tbody>
        {daemonHealth.allDaemonStatuses
          .filter((daemon) => daemon.required)
          .map((daemon) => {
            return (
              <tr key={daemon.daemonType}>
                <td>
                  <DaemonLabel daemon={daemon} />
                </td>
                <td>
                  <DaemonHealth daemon={daemon} />
                </td>
                <td>
                  {daemon.lastHeartbeatTime ? (
                    <Group direction="row" spacing={4}>
                      <Timestamp
                        timestamp={{unix: daemon.lastHeartbeatTime}}
                        timeFormat={TIME_FORMAT}
                      />
                      <span>({`${moment.unix(daemon.lastHeartbeatTime).fromNow()}`})</span>
                    </Group>
                  ) : (
                    'Never'
                  )}
                </td>
              </tr>
            );
          })}
      </tbody>
    </Table>
  );
};

export const DAEMON_HEALTH_FRAGMENT = gql`
  fragment DaemonHealthFragment on DaemonHealth {
    id
    allDaemonStatuses {
      id
      daemonType
      required
      healthy
      lastHeartbeatErrors {
        __typename
        ...PythonErrorFragment
      }
      lastHeartbeatTime
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
