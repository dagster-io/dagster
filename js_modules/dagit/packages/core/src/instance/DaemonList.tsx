import {gql} from '@apollo/client';
import {Group, Table} from '@dagster-io/ui';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {Timestamp} from '../app/time/Timestamp';
import {TimeFromNow} from '../ui/TimeFromNow';

import {DaemonHealth} from './DaemonHealth';
import {DaemonStatusForListFragment} from './types/DaemonList.types';

interface DaemonLabelProps {
  daemon: DaemonStatusForListFragment;
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
  daemonStatuses: DaemonStatusForListFragment[] | undefined;
  showTimestampColumn?: boolean;
}

const TIME_FORMAT = {showSeconds: true, showTimezone: false};

export const DaemonList: React.FC<Props> = ({daemonStatuses, showTimestampColumn = true}) => {
  if (!daemonStatuses?.length) {
    return null;
  }

  return (
    <Table>
      <thead>
        <tr>
          <th style={{width: '25%'}}>Daemon</th>
          <th style={{width: '30%'}}>Status</th>
          {showTimestampColumn && <th>Last heartbeat</th>}
        </tr>
      </thead>
      <tbody>
        {daemonStatuses
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
                {showTimestampColumn && (
                  <td>
                    {daemon.lastHeartbeatTime ? (
                      <Group direction="row" spacing={4}>
                        <Timestamp
                          timestamp={{unix: daemon.lastHeartbeatTime}}
                          timeFormat={TIME_FORMAT}
                        />
                        <span>
                          &nbsp;(
                          <TimeFromNow unixTimestamp={daemon.lastHeartbeatTime} />)
                        </span>
                      </Group>
                    ) : (
                      'Never'
                    )}
                  </td>
                )}
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
      ...DaemonStatusForList
    }
  }

  fragment DaemonStatusForList on DaemonStatus {
    id
    daemonType
    required
    healthy
    lastHeartbeatErrors {
      ...PythonErrorFragment
    }
    lastHeartbeatTime
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
