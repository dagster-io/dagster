import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Heading,
  NonIdealState,
  Page,
  PageHeader,
  Spinner,
  Tag,
  TextInput,
  Tooltip,
} from '@dagster-io/ui';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useTrackPageView} from '../app/analytics';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {JobItemWithRuns, JobTable, ScheduleFragment} from '../instance/JobTable';
import {SCHEDULE_FUTURE_TICKS_FRAGMENT} from '../instance/NextTick';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {makeJobKey} from '../runs/QueryfulRunTimeline';
import {RepoSectionHeader} from '../runs/RepoSectionHeader';
import {RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {RunTimeFragment} from '../runs/types/RunTimeFragment';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {SensorSwitchFragment} from '../sensors/types/SensorSwitchFragment';
import {useRepoExpansionState} from '../ui/useRepoExpansionState';

import {REPOSITORY_INFO_FRAGMENT} from './RepositoryInformation';
import {DagsterRepoOption, WorkspaceContext} from './WorkspaceContext';
import {WorkspaceTabs} from './WorkspaceTabs';
import {buildRepoAddress} from './buildRepoAddress';
import {repoAddressAsString} from './repoAddressAsString';
import {RepoAddress} from './types';
import {RecentRunsPerJobQuery} from './types/RecentRunsPerJobQuery';
import {WorkspaceJobsQuery} from './types/WorkspaceJobsQuery';

const JOBS_EXPANSION_STATE_STORAGE_KEY = 'jobs-page-expansion-state';

export const WorkspaceJobsRoot = () => {
  useTrackPageView();

  const [searchValue, setSearchValue] = React.useState('');
  const {expandedKeys, onToggle} = useRepoExpansionState(JOBS_EXPANSION_STATE_STORAGE_KEY);

  const {allRepos, loading} = React.useContext(WorkspaceContext);

  const queryResultOverview = useQuery<WorkspaceJobsQuery>(WORKSPACE_JOBS_QUERY, {
    fetchPolicy: 'network-only',
    notifyOnNetworkStatusChange: true,
  });
  const {data} = queryResultOverview;

  const queryResultLastRuns = useQuery<RecentRunsPerJobQuery>(RECENT_RUNS_PER_JOB_QUERY, {
    fetchPolicy: 'network-only',
    notifyOnNetworkStatusChange: true,
  });
  const {data: recentRunsData} = queryResultLastRuns;

  // Batch up the data and bucket by repo.
  const runsByJob = useRunsByJob(recentRunsData);
  const schedulesAndSensorsByJob = useSchedulesAndSensorsByJob(data);
  const repoBuckets = useRepoBuckets(allRepos, runsByJob, schedulesAndSensorsByJob);

  const sanitizedSearch = searchValue.trim().toLocaleLowerCase();
  const anySearch = sanitizedSearch.length > 0;

  const filteredBySearch = React.useMemo(() => {
    const searchToLower = sanitizedSearch.toLocaleLowerCase();
    return repoBuckets
      .map(({repoAddress, jobs}) => ({
        repoAddress,
        jobs: jobs.filter(({name}) => name.toLocaleLowerCase().includes(searchToLower)),
      }))
      .filter(({jobs}) => jobs.length > 0);
  }, [repoBuckets, sanitizedSearch]);

  const content = () => {
    if (!filteredBySearch.length) {
      if (anySearch) {
        return (
          <Box padding={{top: 20}}>
            <NonIdealState
              icon="search"
              title="No matching jobs"
              description={
                <div>
                  No jobs matching <strong>{searchValue}</strong> were found in this workspace
                </div>
              }
            />
          </Box>
        );
      }

      return (
        <Box padding={{top: 20}}>
          <NonIdealState
            icon="search"
            title="No jobs"
            description="No jobs were found in this workspace"
          />
        </Box>
      );
    }

    return filteredBySearch.map(({repoAddress, jobs}) => {
      const repoKey = repoAddressAsString(repoAddress);
      const expanded = anySearch || expandedKeys.includes(repoKey);
      const jobCount = jobs.length;
      const tooltipContent = () => {
        if (anySearch) {
          return jobCount === 1 ? `1 matching job` : `${jobCount} matching jobs`;
        }
        return jobCount === 1 ? '1 job' : `${jobCount} jobs`;
      };

      return (
        <div key={repoKey} style={{width: '100%'}}>
          <RepoSectionHeader
            repoName={repoAddress.name}
            repoLocation={repoAddress.location}
            expanded={expanded}
            onClick={() => {
              if (!anySearch) {
                onToggle(repoAddress);
              }
            }}
            showLocation={false}
            rightElement={
              <Tooltip
                content={<span style={{whiteSpace: 'nowrap'}}>{tooltipContent()}</span>}
                placement="top"
              >
                <Tag intent="primary">{jobCount}</Tag>
              </Tooltip>
            }
          />
          {expanded ? <JobTable jobs={jobs} /> : null}
        </div>
      );
    });
  };

  return (
    <Page>
      <PageHeader title={<Heading>Workspace</Heading>} tabs={<WorkspaceTabs tab="jobs" />} />
      {loading && !allRepos.length ? (
        <Box padding={64}>
          <Spinner purpose="page" />
        </Box>
      ) : (
        <>
          <Box
            padding={{horizontal: 24, top: 16}}
            flex={{direction: 'row', alignItems: 'center', gap: 12, grow: 0}}
          >
            {allRepos.length > 1 ? <RepoFilterButton /> : null}
            <TextInput
              icon="search"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              placeholder="Filter by job name…"
              style={{width: '340px'}}
            />
          </Box>
          <Box padding={{top: 20}}>{content()}</Box>
        </>
      )}
    </Page>
  );
};

type ScheduelesAndSensorsByJob = {
  [key: string]: {schedules: ScheduleFragment[]; sensors: SensorSwitchFragment[]};
};

const useSchedulesAndSensorsByJob = (
  data: WorkspaceJobsQuery | undefined,
): ScheduelesAndSensorsByJob => {
  return React.useMemo(() => {
    if (!data || data?.workspaceOrError.__typename !== 'Workspace') {
      return {};
    }

    const byJobKey = {};
    data.workspaceOrError.locationEntries.forEach((entry) => {
      if (entry.locationOrLoadError?.__typename !== 'RepositoryLocation') {
        return;
      }

      const location = entry.locationOrLoadError;
      entry.locationOrLoadError.repositories.forEach((repo) => {
        const repoAddress = buildRepoAddress(repo.name, location.name);
        repo.schedules.forEach((schedule) => {
          const jobKey = makeJobKey(repoAddress, schedule.pipelineName);
          const dataForJob = {...(byJobKey[jobKey] || {schedules: [], sensors: []})};
          dataForJob.schedules.push(schedule);
          byJobKey[jobKey] = dataForJob;
        });
        repo.sensors.forEach((sensor) => {
          (sensor?.targets || []).forEach((target) => {
            const jobKey = makeJobKey(repoAddress, target.pipelineName);
            const dataForJob = {...(byJobKey[jobKey] || {schedules: [], sensors: []})};
            dataForJob.sensors.push(sensor);
            byJobKey[jobKey] = dataForJob;
          });
        });
      });
    });

    return byJobKey;
  }, [data]);
};

type RunsByJob = {
  [jobKey: string]: RunTimeFragment[];
};

const useRunsByJob = (recentRunsData: RecentRunsPerJobQuery | undefined): RunsByJob => {
  return React.useMemo(() => {
    if (!recentRunsData || recentRunsData?.workspaceOrError.__typename !== 'Workspace') {
      return {};
    }

    const byJobKey = {};
    recentRunsData.workspaceOrError.locationEntries.forEach((entry) => {
      if (entry.locationOrLoadError?.__typename !== 'RepositoryLocation') {
        return;
      }
      const location = entry.locationOrLoadError;
      entry.locationOrLoadError.repositories.forEach((repo) => {
        const repoAddress = buildRepoAddress(repo.name, location.name);
        repo.pipelines.forEach((job) => {
          const jobKey = makeJobKey(repoAddress, job.name);
          byJobKey[jobKey] = job.runs;
        });
      });
    });

    return byJobKey;
  }, [recentRunsData]);
};

type RepoBucket = {
  repoAddress: RepoAddress;
  jobs: JobItemWithRuns[];
};

const useRepoBuckets = (
  allRepos: DagsterRepoOption[],
  runsByJob: RunsByJob,
  schedulesAndSensorsByJob: ScheduelesAndSensorsByJob,
): RepoBucket[] => {
  return React.useMemo(() => {
    return [...allRepos]
      .sort((a, b) =>
        a.repository.name.toLocaleLowerCase().localeCompare(b.repository.name.toLocaleLowerCase()),
      )
      .map((repo) => {
        const {name, pipelines} = repo.repository;
        const repoAddress = buildRepoAddress(name, repo.repositoryLocation.name);
        return {
          repoAddress,
          jobs: pipelines
            .filter(({name}) => !isHiddenAssetGroupJob(name))
            .map((pipeline) => {
              const jobKey = makeJobKey(repoAddress, pipeline.name);
              const dataForJob = schedulesAndSensorsByJob[jobKey];

              return {
                isJob: pipeline.isJob,
                name: pipeline.name,
                repoAddress,
                schedules: dataForJob?.schedules || [],
                sensors: dataForJob?.sensors || [],
                runs: runsByJob[jobKey] || [],
              };
            }),
        };
      })
      .filter((repo) => repo.jobs.length > 0);
  }, [allRepos, runsByJob, schedulesAndSensorsByJob]);
};

const WORKSPACE_JOB_FRAGMENT = gql`
  fragment WorkspaceJobFragment on Pipeline {
    id
    name
    isJob
    modes {
      id
      name
    }
  }
`;

export const WORKSPACE_JOBS_QUERY = gql`
  query WorkspaceJobsQuery {
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
                  ...WorkspaceJobFragment
                }
                ...RepositoryInfoFragment
                schedules {
                  id
                  name
                  pipelineName
                  scheduleState {
                    id
                    status
                  }
                  ...ScheduleFutureTicksFragment
                  ...ScheduleSwitchFragment
                }
                sensors {
                  id
                  name
                  targets {
                    pipelineName
                  }
                  sensorState {
                    id
                    status
                  }
                  ...SensorSwitchFragment
                }
              }
            }
            ...PythonErrorFragment
          }
        }
      }
      ...PythonErrorFragment
    }
  }

  ${WORKSPACE_JOB_FRAGMENT}
  ${REPOSITORY_INFO_FRAGMENT}
  ${SCHEDULE_FUTURE_TICKS_FRAGMENT}
  ${SCHEDULE_SWITCH_FRAGMENT}
  ${SENSOR_SWITCH_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const RECENT_RUNS_PER_JOB_QUERY = gql`
  query RecentRunsPerJobQuery {
    workspaceOrError {
      ... on Workspace {
        locationEntries {
          id
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
                  runs(limit: 5) {
                    id
                    ...RunTimeFragment
                  }
                }
              }
            }
            ...PythonErrorFragment
          }
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${RUN_TIME_FRAGMENT}
`;
