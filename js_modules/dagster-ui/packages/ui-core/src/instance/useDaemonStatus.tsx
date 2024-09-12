import {useMemo} from 'react';

import {StatusAndMessage} from './DeploymentStatusType';
import {INSTANCE_HEALTH_FRAGMENT} from './InstanceHealthFragment';
import {InstanceWarningQuery, InstanceWarningQueryVariables} from './types/useDaemonStatus.types';
import {gql, useQuery} from '../apollo-client';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {InstigationStatus} from '../graphql/types';
import {useRepositoryOptions} from '../workspace/WorkspaceContext/util';

export const useDaemonStatus = (skip = false): StatusAndMessage | null => {
  const {options} = useRepositoryOptions();
  const queryResult = useQuery<InstanceWarningQuery, InstanceWarningQueryVariables>(
    INSTANCE_WARNING_QUERY,
    {
      notifyOnNetworkStatusChange: true,
      skip,
      blocking: false,
    },
  );

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS, !skip);

  const {data: healthData} = queryResult;

  const {anySchedules, anySensors} = useMemo(() => {
    let anySchedules = false;
    let anySensors = false;

    // Find any schedules or sensors in the repo list.
    for (const repo of options) {
      if (repo.repository.sensors.some((s) => s.sensorState.status === InstigationStatus.RUNNING)) {
        anySensors = true;
        break;
      }
    }
    for (const repo of options) {
      if (
        repo.repository.schedules.some((s) => s.scheduleState.status === InstigationStatus.RUNNING)
      ) {
        anySchedules = true;
        break;
      }
    }

    return {anySchedules, anySensors};
  }, [options]);

  const visibleErrorCount = useMemo(() => {
    const allDaemons = healthData?.instance.daemonHealth.allDaemonStatuses;
    if (!allDaemons) {
      return 0;
    }

    const anyRequestedBackfills =
      healthData?.partitionBackfillsOrError.__typename === 'PartitionBackfills'
        ? healthData.partitionBackfillsOrError.results.length > 0
        : false;

    const errors = allDaemons
      .filter((daemon) => !daemon.healthy && daemon.required)
      .reduce((accum, daemon) => accum.add(daemon.daemonType), new Set<string>());

    const totalErrorCount = errors.size;
    const scheduleError = anySchedules && errors.has('SCHEDULER');
    const sensorError = anySensors && errors.has('SENSOR');
    const backfillsError = anyRequestedBackfills && errors.has('BACKFILL');

    errors.delete('SCHEDULER');
    errors.delete('SENSOR');
    errors.delete('BACKFILL');

    // If there are any errors besides scheduler/sensor/backfill, show the entire count.
    if (errors.size) {
      return totalErrorCount;
    }

    // Otherwise, just show the number that is relevant to the user's workspace.
    // - If there are no schedules or sensors, this will be zero.
    // - If there is a sensor daemon error but there are no sensors, this will be zero.
    // - If there is a backfill daemon error but there are no backfills, this will be zero.
    return Number(scheduleError) + Number(sensorError) + Number(backfillsError);
  }, [anySchedules, anySensors, healthData]);

  if (visibleErrorCount) {
    return {
      type: 'warning',
      content: (
        <div style={{whiteSpace: 'nowrap'}}>{`${visibleErrorCount} ${
          visibleErrorCount === 1 ? 'daemon not running' : 'daemons not running'
        }`}</div>
      ),
    };
  }

  return null;
};

export const INSTANCE_WARNING_QUERY = gql`
  query InstanceWarningQuery {
    instance {
      id
      ...InstanceHealthFragment
    }
    partitionBackfillsOrError(status: REQUESTED) {
      ... on PartitionBackfills {
        results {
          id
        }
      }
    }
  }

  ${INSTANCE_HEALTH_FRAGMENT}
`;
