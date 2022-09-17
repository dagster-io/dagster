import {gql, useQuery} from '@apollo/client';
import {Box, Colors, Icon, PageHeader, Spinner, Heading, TextInput} from '@dagster-io/ui';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useMergedRefresh, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {
  failedStatuses,
  inProgressStatuses,
  queuedStatuses,
  successStatuses,
} from '../runs/RunStatuses';
import {RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {RunTimeFragment} from '../runs/types/RunTimeFragment';
import {makeJobKey} from '../runs/useRunsForTimeline';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {REPOSITORY_INFO_FRAGMENT} from '../workspace/RepositoryInformation';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';
import {JobItem, JobItemWithRuns, JobTable} from './JobTable';
import {SCHEDULE_FUTURE_TICKS_FRAGMENT} from './NextTick';
import {RepoFilterButton} from './RepoFilterButton';
import {RunTimelineSection} from './RunTimelineSection';
import {
  InstanceOverviewInitialQuery,
  InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules as Schedule,
  InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors as Sensor,
} from './types/InstanceOverviewInitialQuery';
import {LastTenRunsPerJobQuery} from './types/LastTenRunsPerJobQuery';

type State = {
  searchValue: string;
};

type Action = {type: 'search'; value: string};

const reducer = (state: State, action: Action) => {
  switch (action.type) {
    case 'search': {
      return {...state, searchValue: action.value};
    }
    default:
      return state;
  }
};

const initialState: State = {
  searchValue: '',
};

export const InstanceOverviewPage = () => {
  useTrackPageView();

  const [state, dispatch] = React.useReducer(reducer, initialState);

  const {pageTitle} = React.useContext(InstancePageContext);
  const {allRepos, visibleRepos} = React.useContext(WorkspaceContext);
  const {searchValue} = state;

  const queryResultOverview = useQuery<InstanceOverviewInitialQuery>(
    INSTANCE_OVERVIEW_INITIAL_QUERY,
    {
      fetchPolicy: 'network-only',
      notifyOnNetworkStatusChange: true,
    },
  );
  const {data, loading} = queryResultOverview;

  const queryResultLastRuns = useQuery<LastTenRunsPerJobQuery>(LAST_TEN_RUNS_PER_JOB_QUERY, {
    fetchPolicy: 'network-only',
    notifyOnNetworkStatusChange: true,
  });
  const {data: lastTenRunsData} = queryResultLastRuns;

  const refreshState = useMergedRefresh(
    useQueryRefreshAtInterval(queryResultLastRuns, FIFTEEN_SECONDS),
    useQueryRefreshAtInterval(queryResultOverview, FIFTEEN_SECONDS),
  );

  const bucketed = React.useMemo(() => {
    const failed = [];
    const inProgress = [];
    const succeeded = [];
    const queued = [];
    const neverRan = [];

    const sortFn = (a: JobItemWithRuns, b: JobItemWithRuns) => {
      const aRun = a.runs[0] || null;
      const bRun = b.runs[0] || null;

      if (aRun.startTime) {
        return bRun.startTime ? bRun.startTime - aRun.startTime : -1;
      } else if (bRun.startTime) {
        return -1;
      }

      return a.name.toLocaleLowerCase().localeCompare(b.name.toLocaleLowerCase());
    };

    if (data && Object.keys(data).length && data?.workspaceOrError.__typename === 'Workspace') {
      for (const locationEntry of data.workspaceOrError.locationEntries) {
        if (
          locationEntry.__typename === 'WorkspaceLocationEntry' &&
          locationEntry.locationOrLoadError?.__typename === 'RepositoryLocation'
        ) {
          for (const repository of locationEntry.locationOrLoadError.repositories) {
            for (const pipeline of repository.pipelines) {
              const {runs} = pipeline;
              const schedules: Schedule[] = (repository.schedules || []).filter(
                (schedule) => schedule.pipelineName === pipeline.name,
              );
              const sensors: Sensor[] = (repository.sensors || []).filter((sensor) =>
                sensor.targets?.map((t) => t.pipelineName).includes(pipeline.name),
              );
              const repoAddress = buildRepoAddress(
                repository.name,
                locationEntry.locationOrLoadError.name,
              );

              if (runs.length) {
                const {status} = runs[0];
                const item: JobItemWithRuns = {
                  isJob: pipeline.isJob,
                  name: pipeline.name,
                  schedules,
                  sensors,
                  repoAddress,
                  runs,
                };
                if (failedStatuses.has(status)) {
                  failed.push(item);
                } else if (inProgressStatuses.has(status)) {
                  inProgress.push(item);
                } else if (successStatuses.has(status)) {
                  succeeded.push(item);
                } else if (queuedStatuses.has(status)) {
                  queued.push(item);
                } else {
                  neverRan.push(item);
                }
              }
            }
          }
        }
      }
    }

    failed.sort(sortFn);
    inProgress.sort(sortFn);
    queued.sort(sortFn);
    succeeded.sort(sortFn);
    neverRan.sort(sortFn);

    return {failed, inProgress, queued, succeeded, neverRan};
  }, [data]);

  const filteredJobs = React.useMemo(() => {
    const searchToLower = searchValue.toLocaleLowerCase();
    const filterJobs = ({name, repoAddress}: JobItem) =>
      visibleRepos.some(
        (r) =>
          r.repository.name === repoAddress.name &&
          r.repositoryLocation.name === repoAddress.location,
      ) &&
      name.toLocaleLowerCase().includes(searchToLower) &&
      !isHiddenAssetGroupJob(name);

    const {failed, inProgress, queued, succeeded, neverRan} = bucketed;
    return {
      failed: failed.filter(filterJobs),
      inProgress: inProgress.filter(filterJobs),
      queued: queued.filter(filterJobs),
      succeeded: succeeded.filter(filterJobs),
      neverRan: neverRan.filter(filterJobs),
    };
  }, [bucketed, visibleRepos, searchValue]);

  const lastTenRunsFlattened = React.useMemo(() => {
    if (!lastTenRunsData || Object.keys(lastTenRunsData).length === 0) {
      return null;
    }

    const flattened: {[key: string]: RunTimeFragment[]} = {};
    if (lastTenRunsData.workspaceOrError.__typename === 'Workspace') {
      for (const locationEntry of lastTenRunsData.workspaceOrError.locationEntries) {
        if (
          locationEntry.__typename === 'WorkspaceLocationEntry' &&
          locationEntry.locationOrLoadError?.__typename === 'RepositoryLocation'
        ) {
          for (const repository of locationEntry.locationOrLoadError.repositories) {
            for (const pipeline of repository.pipelines) {
              const jobKey = makeJobKey(
                buildRepoAddress(repository.name, locationEntry.locationOrLoadError.name),
                pipeline.name,
              );
              flattened[jobKey] = pipeline.runs;
            }
          }
        }
      }
    }

    return flattened;
  }, [lastTenRunsData]);

  const visibleJobKeys: Set<string> = React.useMemo(() => {
    const jobKeys = Object.values(filteredJobs)
      .flat()
      .map((jobItem) => makeJobKey(jobItem.repoAddress, jobItem.name));
    return new Set(jobKeys);
  }, [filteredJobs]);

  const filteredJobsWithRuns = React.useMemo(() => {
    const appendRuns = (jobItem: JobItem) => {
      const {name, repoAddress} = jobItem;
      const jobKey = makeJobKey(repoAddress, name);
      const matchingRuns = lastTenRunsFlattened ? lastTenRunsFlattened[jobKey] || [] : [];
      return {...jobItem, runs: [...matchingRuns].reverse()};
    };

    const {failed, inProgress, queued, succeeded, neverRan} = filteredJobs;
    return {
      failed: failed.map(appendRuns),
      inProgress: inProgress.map(appendRuns),
      queued: queued.map(appendRuns),
      succeeded: succeeded.map(appendRuns),
      neverRan: neverRan.map(appendRuns),
    };
  }, [lastTenRunsFlattened, filteredJobs]);

  if (!data || Object.keys(data).length === 0) {
    return (
      <>
        <PageHeader
          title={<Heading>{pageTitle}</Heading>}
          tabs={<InstanceTabs tab="overview" refreshState={refreshState} />}
        />
        <Box padding={64}>
          <Spinner purpose="section" />
        </Box>
      </>
    );
  }

  const {failed, inProgress, queued, succeeded, neverRan} = filteredJobsWithRuns;

  return (
    <>
      <PageHeader
        title={<Heading>{pageTitle}</Heading>}
        tabs={<InstanceTabs tab="overview" refreshState={refreshState} />}
      />
      <Box
        padding={{horizontal: 24, top: 16}}
        flex={{direction: 'row', alignItems: 'center', gap: 12, grow: 0}}
      >
        {allRepos.length > 1 && <RepoFilterButton />}
        <TextInput
          icon="search"
          value={searchValue}
          onChange={(e) => dispatch({type: 'search', value: e.target.value})}
          placeholder="Filter by job name…"
          style={{width: '340px'}}
        />
      </Box>
      <RunTimelineSection loading={loading} visibleJobKeys={visibleJobKeys} />
      {inProgress.length ? (
        <JobSection
          icon={<Icon name="hourglass_bottom" color={Colors.Blue500} size={24} />}
          heading={
            inProgress.length === 1 ? '1 job in progress' : `${inProgress.length} jobs in progress`
          }
          jobs={inProgress}
        />
      ) : null}
      {failed.length ? (
        <JobSection
          icon={<Icon name="error_outline" color={Colors.Red500} size={24} />}
          heading={failed.length === 1 ? '1 job failed' : `${failed.length} jobs failed`}
          jobs={failed}
        />
      ) : null}
      {queued.length ? (
        <JobSection
          icon={<Icon name="checklist" color={Colors.Gray500} size={24} />}
          heading={queued.length === 1 ? '1 job queued' : `${queued.length} jobs queued`}
          jobs={queued}
        />
      ) : null}
      {succeeded.length ? (
        <JobSection
          icon={<Icon name="check_circle" color={Colors.Green500} size={24} />}
          heading={
            succeeded.length === 1 ? '1 job succeeded' : `${succeeded.length} jobs succeeded`
          }
          jobs={succeeded}
        />
      ) : null}
      {neverRan.length ? (
        <JobSection
          icon={<Icon name="history_toggle_off" color={Colors.Gray900} size={24} />}
          heading={neverRan.length === 1 ? '1 job never ran' : `${neverRan.length} jobs never ran`}
          jobs={neverRan}
        />
      ) : null}
    </>
  );
};

interface JobSectionProps {
  icon: React.ReactNode;
  heading: React.ReactNode;
  jobs: JobItemWithRuns[];
}

const JobSection = (props: JobSectionProps) => {
  const {icon, heading, jobs} = props;
  return (
    <>
      <Box
        flex={{direction: 'row', gap: 8, alignItems: 'center'}}
        margin={{top: 16}}
        padding={{vertical: 16, horizontal: 24}}
      >
        {icon}
        <Heading>{heading}</Heading>
      </Box>
      <JobTable jobs={jobs} />
    </>
  );
};

const OVERVIEW_JOB_FRAGMENT = gql`
  fragment OverviewJobFragment on Pipeline {
    id
    name
    isJob
    runs(limit: 1) {
      id
      runId
      status
      ...RunTimeFragment
    }
  }

  ${RUN_TIME_FRAGMENT}
`;

export const INSTANCE_OVERVIEW_INITIAL_QUERY = gql`
  query InstanceOverviewInitialQuery {
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
                  ...OverviewJobFragment
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

  ${OVERVIEW_JOB_FRAGMENT}
  ${REPOSITORY_INFO_FRAGMENT}
  ${SCHEDULE_FUTURE_TICKS_FRAGMENT}
  ${SCHEDULE_SWITCH_FRAGMENT}
  ${SENSOR_SWITCH_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const LAST_TEN_RUNS_PER_JOB_QUERY = gql`
  query LastTenRunsPerJobQuery {
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
                  runs(limit: 10) {
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
