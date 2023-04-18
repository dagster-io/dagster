import {gql, useQuery, useMutation} from '@apollo/client';
import {Box, Checkbox, Group, Spinner, Table, Tag} from '@dagster-io/ui';
import * as React from 'react';

import {useConfirmation} from '../app/CustomConfirmationProvider';
import {useUnscopedPermissions} from '../app/Permissions';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {Timestamp} from '../app/time/Timestamp';
import {TimeFromNow} from '../ui/TimeFromNow';

import {DaemonHealth} from './DaemonHealth';
import {
  DaemonStatusForListFragment,
  GetAutoMaterializePausedQuery,
  GetAutoMaterializePausedQueryVariables,
  SetAutoMaterializePausedMutation,
  SetAutoMaterializePausedMutationVariables,
} from './types/DaemonList.types';

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
  const {data, loading, refetch} = useQuery<
    GetAutoMaterializePausedQuery,
    GetAutoMaterializePausedQueryVariables
  >(AUTOMATERIALIZE_PAUSED_QUERY);

  const [setAutoMaterializePaused] = useMutation<
    SetAutoMaterializePausedMutation,
    SetAutoMaterializePausedMutationVariables
  >(SET_AUTOMATERIALIZE_PAUSED_MUTATION, {
    onCompleted: () => {
      refetch();
    },
  });

  const assetDaemon = daemonStatuses?.filter((daemon) => daemon.daemonType === 'ASSET')[0];
  const nonAssetDaemons = daemonStatuses?.filter((daemon) => daemon.daemonType !== 'ASSET');

  const confirm = useConfirmation();

  const {permissions: {canToggleAutoMaterialize} = {}} = useUnscopedPermissions();

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
        {assetDaemon ? (
          <tr>
            <td>
              <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                Auto-materializing
                {loading ? (
                  <Spinner purpose="body-text" />
                ) : (
                  <Checkbox
                    format="switch"
                    checked={!data?.instance?.autoMaterializePaused}
                    disabled={!canToggleAutoMaterialize}
                    onChange={async (e) => {
                      const checked = e.target.checked;
                      if (!checked) {
                        await confirm({
                          title: 'Pause Auto-materializing?',
                          description:
                            'Pausing Auto-materializing will prevent new materializations triggered by an Auto-materializing policy.',
                        });
                      }
                      setAutoMaterializePaused({
                        variables: {
                          paused: !checked,
                        },
                      });
                    }}
                  />
                )}
              </Box>
            </td>
            <td>
              {data?.instance.autoMaterializePaused ? (
                <Tag intent="warning">Paused</Tag>
              ) : (
                <DaemonHealth daemon={assetDaemon} />
              )}
            </td>
            {showTimestampColumn && (
              <td>
                {assetDaemon.lastHeartbeatTime ? (
                  <Group direction="row" spacing={4}>
                    <Timestamp
                      timestamp={{unix: assetDaemon.lastHeartbeatTime}}
                      timeFormat={TIME_FORMAT}
                    />
                    <span>
                      <TimeFromNow unixTimestamp={assetDaemon.lastHeartbeatTime} />
                    </span>
                  </Group>
                ) : (
                  'Never'
                )}
              </td>
            )}
          </tr>
        ) : null}
        {nonAssetDaemons
          ?.filter((daemon) => daemon.required)
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
                          <TimeFromNow unixTimestamp={daemon.lastHeartbeatTime} />
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

export const AUTOMATERIALIZE_PAUSED_QUERY = gql`
  query GetAutoMaterializePausedQuery {
    instance {
      id
      autoMaterializePaused
    }
  }
`;

export const SET_AUTOMATERIALIZE_PAUSED_MUTATION = gql`
  mutation SetAutoMaterializePausedMutation($paused: Boolean!) {
    setAutoMaterializePaused(paused: $paused)
  }
`;
