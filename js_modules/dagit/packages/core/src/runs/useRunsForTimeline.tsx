import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {SCHEDULE_FUTURE_TICKS_FRAGMENT} from '../instance/NextTick';
import {InstigationStatus, RunsFilter, RunStatus} from '../types/globalTypes';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath} from '../workspace/workspacePath';

import {doneStatuses} from './RunStatuses';
import {TimelineJob, TimelineRun} from './RunTimeline';
import {RUN_TIME_FRAGMENT} from './RunUtils';
import {overlap} from './batchRunsForTimeline';
import {RunTimelineQuery, RunTimelineQueryVariables} from './types/RunTimelineQuery';

export const useRunsForTimeline = (range: [number, number], runsFilter: RunsFilter = {}) => {
  const [start, end] = range;

  const {data, previousData, loading} = useQuery<RunTimelineQuery, RunTimelineQueryVariables>(
    RUN_TIMELINE_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      notifyOnNetworkStatusChange: true,
      variables: {
        inProgressFilter: {
          ...runsFilter,
          statuses: [RunStatus.CANCELING, RunStatus.STARTED],
          createdBefore: end / 1000.0,
        },
        terminatedFilter: {
          ...runsFilter,
          statuses: Array.from(doneStatuses),
          createdBefore: end / 1000.0,
          updatedAfter: start / 1000.0,
        },
      },
    },
  );

  const {unterminated, terminated, workspaceOrError} = data || previousData || {};

  const runsByJobKey = React.useMemo(() => {
    const map: {[jobKey: string]: TimelineRun[]} = {};
    const now = Date.now();

    // fetch all the runs in the given range
    [
      ...(unterminated?.__typename === 'Runs' ? unterminated.results : []),
      ...(terminated?.__typename === 'Runs' ? terminated.results : []),
    ].forEach((run) => {
      if (!run.startTime) {
        return;
      }
      if (!run.repositoryOrigin) {
        return;
      }

      if (
        !overlap(
          {start, end},
          {
            start: run.startTime * 1000,
            end: run.endTime ? run.endTime * 1000 : now,
          },
        )
      ) {
        return;
      }

      const runJobKey = makeJobKey(
        {
          name: run.repositoryOrigin.repositoryName,
          location: run.repositoryOrigin.repositoryLocationName,
        },
        run.pipelineName,
      );

      map[runJobKey] = [
        ...(map[runJobKey] || []),
        {
          id: run.id,
          status: run.status,
          startTime: run.startTime * 1000,
          endTime: run.endTime ? run.endTime * 1000 : now,
        },
      ];
    });

    return map;
  }, [end, unterminated, terminated, start]);

  const jobsWithRuns: TimelineJob[] = React.useMemo(() => {
    if (!workspaceOrError || workspaceOrError.__typename !== 'Workspace') {
      return [];
    }

    const jobs = [];
    for (const locationEntry of workspaceOrError.locationEntries) {
      if (
        locationEntry.__typename !== 'WorkspaceLocationEntry' ||
        locationEntry.locationOrLoadError?.__typename !== 'RepositoryLocation'
      ) {
        continue;
      }

      for (const repository of locationEntry.locationOrLoadError.repositories) {
        const repoAddress = buildRepoAddress(
          repository.name,
          locationEntry.locationOrLoadError.name,
        );

        for (const pipeline of repository.pipelines) {
          const schedules = (repository.schedules || []).filter(
            (schedule) => schedule.pipelineName === pipeline.name,
          );

          const jobTicks: TimelineRun[] = [];
          for (const schedule of schedules) {
            if (schedule.scheduleState.status === InstigationStatus.RUNNING) {
              schedule.futureTicks.results.forEach(({timestamp}) => {
                const startTime = timestamp * 1000;
                if (overlap({start, end}, {start: startTime, end: startTime})) {
                  jobTicks.push({
                    id: `${schedule.pipelineName}-future-run-${timestamp}`,
                    status: 'SCHEDULED',
                    startTime,
                    endTime: startTime + 10 * 1000,
                  });
                }
              });
            }
          }

          const isAdHoc = isHiddenAssetGroupJob(pipeline.name);
          const jobKey = makeJobKey(repoAddress, pipeline.name);
          const jobName = isAdHoc ? 'Ad hoc materializations' : pipeline.name;

          const jobRuns = runsByJobKey[jobKey] || [];
          if (jobTicks.length || jobRuns.length) {
            jobs.push({
              key: jobKey,
              jobName,
              jobType: isAdHoc ? 'asset' : 'job',
              repoAddress,
              path: workspacePipelinePath({
                repoName: repoAddress.name,
                repoLocation: repoAddress.location,
                pipelineName: pipeline.name,
                isJob: pipeline.isJob,
              }),
              runs: [...jobRuns, ...jobTicks],
            } as TimelineJob);
          }
        }
      }
    }

    const earliest = jobs.reduce((accum, job) => {
      const startTimes = job.runs.map((job) => job.startTime);
      return {...accum, [job.key]: Math.min(...startTimes)};
    }, {} as {[jobKey: string]: number});

    return jobs.sort((a, b) => earliest[a.key] - earliest[b.key]);
  }, [workspaceOrError, runsByJobKey, start, end]);

  return {
    jobs: jobsWithRuns,
    loading: loading && !data && !previousData,
  };
};

export const makeJobKey = (repoAddress: RepoAddress, jobName: string) =>
  `${jobName}-${repoAddressAsString(repoAddress)}`;

const RUN_TIMELINE_QUERY = gql`
  query RunTimelineQuery($inProgressFilter: RunsFilter!, $terminatedFilter: RunsFilter!) {
    unterminated: runsOrError(filter: $inProgressFilter) {
      ... on Runs {
        results {
          id
          pipelineName
          repositoryOrigin {
            id
            repositoryName
            repositoryLocationName
          }
          ...RunTimeFragment
        }
      }
    }
    terminated: runsOrError(filter: $terminatedFilter) {
      ... on Runs {
        results {
          id
          pipelineName
          repositoryOrigin {
            id
            repositoryName
            repositoryLocationName
          }
          ...RunTimeFragment
        }
      }
    }
    workspaceOrError {
      ... on Workspace {
        locationEntries {
          id
          name
          loadStatus
          displayMetadata {
            key
            value
          }
          locationOrLoadError {
            ... on RepositoryLocation {
              id
              name
              repositories {
                id
                name
                pipelines {
                  id
                  name
                  isJob
                }
                schedules {
                  id
                  name
                  pipelineName
                  scheduleState {
                    id
                    status
                  }
                  ...ScheduleFutureTicksFragment
                }
              }
            }
          }
        }
      }
    }
  }
  ${RUN_TIME_FRAGMENT}
  ${SCHEDULE_FUTURE_TICKS_FRAGMENT}
`;
