import {sortRepoBuckets} from '../overview/sortRepoBuckets';
import {WorkspaceLocationNodeFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

export const buildAutomationRepoBuckets = (
  locationEntries: Extract<WorkspaceLocationNodeFragment, {__typename: 'WorkspaceLocationEntry'}>[],
) => {
  const entries = locationEntries.map((entry) => entry.locationOrLoadError);

  const buckets = [];

  for (const entry of entries) {
    if (entry?.__typename !== 'RepositoryLocation') {
      continue;
    }

    for (const repo of entry.repositories) {
      const {name, schedules, sensors} = repo;
      const repoAddress = buildRepoAddress(name, entry.name);

      if (sensors.length > 0 || schedules.length > 0) {
        buckets.push({
          repoAddress,
          schedules: schedules.map((schedule) => ({
            ...schedule,
            type: 'schedule' as const,
            status:
              schedule.scheduleState.status === 'RUNNING'
                ? ('running' as const)
                : ('stopped' as const),
            tags: schedule.tags,
            repo: repoAddress,
          })),
          sensors: sensors.map((sensor) => ({
            ...sensor,
            type: 'sensor' as const,
            status:
              sensor.sensorState.status === 'RUNNING' ? ('running' as const) : ('stopped' as const),
            tags: sensor.tags,
            repo: repoAddress,
          })),
        });
      }
    }
  }

  return sortRepoBuckets(buckets);
};
