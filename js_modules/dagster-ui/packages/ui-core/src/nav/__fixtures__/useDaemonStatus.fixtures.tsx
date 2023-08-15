import {MockedResponse} from '@apollo/client/testing';

import {
  buildWorkspace,
  buildWorkspaceLocationEntry,
  buildRepositoryLocation,
  buildRepository,
  buildSchedule,
  buildInstigationState,
  InstigationStatus,
  buildSensor,
  buildInstance,
  buildDaemonHealth,
  buildDaemonStatus,
  buildPartitionBackfills,
  buildPartitionBackfill,
} from '../../graphql/types';
import {InstanceWarningQuery} from '../../instance/types/useDaemonStatus.types';
import {INSTANCE_WARNING_QUERY} from '../../instance/useDaemonStatus';
import {ROOT_WORKSPACE_QUERY} from '../../workspace/WorkspaceContext';
import {RootWorkspaceQuery} from '../../workspace/types/WorkspaceContext.types';

const buildRepo = ({
  name,
  schedules = {},
  sensors = {},
}: {
  name: string;
  schedules?: Record<string, InstigationStatus>;
  sensors?: Record<string, InstigationStatus>;
}) => {
  return buildRepository({
    id: name,
    name,
    schedules: Object.keys(schedules).map((scheduleName) =>
      buildSchedule({
        id: scheduleName,
        name: scheduleName,
        scheduleState: buildInstigationState({
          id: `instigation-state-${scheduleName}`,
          status: schedules[scheduleName],
        }),
      }),
    ),
    sensors: Object.keys(sensors).map((sensorName) =>
      buildSensor({
        id: sensorName,
        name: sensorName,
        sensorState: buildInstigationState({
          id: `instigation-state-${sensorName}`,
          status: sensors[sensorName],
        }),
      }),
    ),
  });
};

export const buildWorkspaceQueryWithNoSchedulesOrSensors = (): MockedResponse<RootWorkspaceQuery> => {
  return {
    request: {
      query: ROOT_WORKSPACE_QUERY,
      variables: {},
    },
    result: {
      data: {
        __typename: 'Query',
        workspaceOrError: buildWorkspace({
          locationEntries: [
            buildWorkspaceLocationEntry({
              id: 'ipsum-entry',
              name: 'ipsum-entry',
              locationOrLoadError: buildRepositoryLocation({
                id: 'ipsum',
                name: 'ipsum',
                repositories: [buildRepo({name: 'lorem'})],
              }),
            }),
          ],
        }),
      },
    },
  };
};

export const buildWorkspaceQueryWithScheduleAndSensor = ({
  schedule,
  sensor,
}: {
  schedule: InstigationStatus;
  sensor: InstigationStatus;
}): MockedResponse<RootWorkspaceQuery> => {
  return {
    request: {
      query: ROOT_WORKSPACE_QUERY,
      variables: {},
    },
    result: {
      data: {
        __typename: 'Query',
        workspaceOrError: buildWorkspace({
          locationEntries: [
            buildWorkspaceLocationEntry({
              id: 'ipsum-entry',
              name: 'ipsum-entry',
              locationOrLoadError: buildRepositoryLocation({
                id: 'ipsum',
                name: 'ipsum',
                repositories: [
                  buildRepo({
                    name: 'lorem',
                    schedules: {'my-schedule': schedule},
                    sensors: {'my-sensor': sensor},
                  }),
                ],
              }),
            }),
          ],
        }),
      },
    },
  };
};

type DaemonHealth = {daemonType: string; healthy: boolean; required: boolean}[];

export const buildInstanceWarningQuery = (
  daemonHealth: DaemonHealth,
  backfillCount = 0,
): MockedResponse<InstanceWarningQuery> => {
  return {
    request: {
      query: INSTANCE_WARNING_QUERY,
      variables: {},
    },
    result: {
      data: {
        __typename: 'Query',
        instance: buildInstance({
          daemonHealth: buildDaemonHealth({
            id: 'daemon-health',
            allDaemonStatuses: daemonHealth.map(({daemonType, healthy, required}) =>
              buildDaemonStatus({id: `daemon-${daemonType}`, daemonType, healthy, required}),
            ),
          }),
        }),
        partitionBackfillsOrError: buildPartitionBackfills({
          results: new Array(backfillCount).fill(null).map((_, ii) =>
            buildPartitionBackfill({
              id: `backfill-${ii}`,
            }),
          ),
        }),
      },
    },
  };
};
