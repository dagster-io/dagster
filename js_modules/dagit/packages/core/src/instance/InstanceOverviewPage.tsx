import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Button,
  ButtonGroup,
  Colors,
  Icon,
  PageHeader,
  Spinner,
  Table,
  Body,
  Heading,
  TextInput,
  FontFamily,
} from '@dagster-io/ui';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useMergedRefresh, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {ScheduleOrSensorTag} from '../nav/ScheduleOrSensorTag';
import {LegacyPipelineTag} from '../pipelines/LegacyPipelineTag';
import {PipelineReference} from '../pipelines/PipelineReference';
import {HourWindow, makeJobKey, QueryfulRunTimeline} from '../runs/QueryfulRunTimeline';
import {RunStatusPezList} from '../runs/RunStatusPez';
import {
  failedStatuses,
  inProgressStatuses,
  queuedStatuses,
  successStatuses,
} from '../runs/RunStatuses';
import {TimelineJob} from '../runs/RunTimeline';
import {RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {RunTimeFragment} from '../runs/types/RunTimeFragment';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {REPOSITORY_INFO_FRAGMENT} from '../workspace/RepositoryInformation';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath} from '../workspace/workspacePath';

import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';
import {JobMenu} from './JobMenu';
import {LastRunSummary} from './LastRunSummary';
import {NextTick, SCHEDULE_FUTURE_TICKS_FRAGMENT} from './NextTick';
import {RepoFilterButton} from './RepoFilterButton';
import {
  InstanceOverviewInitialQuery,
  InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules as Schedule,
  InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors as Sensor,
} from './types/InstanceOverviewInitialQuery';
import {LastTenRunsPerJobQuery} from './types/LastTenRunsPerJobQuery';
import {OverviewJobFragment} from './types/OverviewJobFragment';

type JobItem = {
  job: OverviewJobFragment;
  repoAddress: RepoAddress;
  schedules: Schedule[];
  sensors: Sensor[];
};

type JobItemWithRuns = JobItem & {
  runs: RunTimeFragment[];
};

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

    const sortFn = (a: JobItem, b: JobItem) => {
      const aRun = a.job.runs[0] || null;
      const bRun = b.job.runs[0] || null;

      if (aRun.startTime) {
        return bRun.startTime ? bRun.startTime - aRun.startTime : -1;
      } else if (bRun.startTime) {
        return -1;
      }

      return a.job.name.toLocaleLowerCase().localeCompare(b.job.name.toLocaleLowerCase());
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
                const item: JobItem = {
                  job: pipeline,
                  schedules,
                  sensors,
                  repoAddress,
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
    const filterJobs = ({job, repoAddress}: JobItem) =>
      visibleRepos.some(
        (r) =>
          r.repository.name === repoAddress.name &&
          r.repositoryLocation.name === repoAddress.location,
      ) &&
      job.name.toLocaleLowerCase().includes(searchToLower) &&
      !isHiddenAssetGroupJob(job.name);

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

  const filteredJobsFlattened: JobItem[] = React.useMemo(() => {
    return Object.values(filteredJobs).reduce((accum, jobList) => {
      return [...accum, ...jobList];
    }, []);
  }, [filteredJobs]);

  const filteredJobsWithRuns = React.useMemo(() => {
    const appendRuns = (jobItem: JobItem) => {
      const {job, repoAddress} = jobItem;
      const jobKey = makeJobKey(repoAddress, job.name);
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
      <RunTimelineSection jobs={filteredJobsFlattened} loading={loading} />
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

const LOOKAHEAD_HOURS = 1;
const ONE_HOUR = 60 * 60 * 1000;

const RunTimelineSection = ({jobs, loading}: {jobs: JobItem[]; loading: boolean}) => {
  const [shown, setShown] = React.useState(true);
  const [hourWindow, setHourWindow] = React.useState<HourWindow>('6');
  const nowRef = React.useRef(Date.now());

  React.useEffect(() => {
    if (!loading) {
      nowRef.current = Date.now();
    }
  }, [loading]);

  const nowSecs = Math.floor(nowRef.current / 1000);
  const range: [number, number] = React.useMemo(() => {
    return [
      nowSecs * 1000 - Number(hourWindow) * ONE_HOUR,
      nowSecs * 1000 + LOOKAHEAD_HOURS * ONE_HOUR,
    ];
  }, [hourWindow, nowSecs]);

  const [start, end] = React.useMemo(() => {
    const [unvalidatedStart, unvalidatedEnd] = range;
    return unvalidatedEnd < unvalidatedStart
      ? [unvalidatedEnd, unvalidatedStart]
      : [unvalidatedStart, unvalidatedEnd];
  }, [range]);

  const timelineJobs: TimelineJob[] = jobs.map((job) => ({
    key: makeJobKey(job.repoAddress, job.job.name),
    jobName: job.job.name,
    repoAddress: job.repoAddress,
    path: workspacePipelinePath({
      repoName: job.repoAddress.name,
      repoLocation: job.repoAddress.location,
      pipelineName: job.job.name,
      isJob: job.job.isJob,
    }),
    runs: [],
  }));

  return (
    <>
      <Box
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
        margin={{top: 16}}
        padding={{bottom: 16, horizontal: 24}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <Box flex={{alignItems: 'center', gap: 8}}>
          <Icon name="waterfall_chart" color={Colors.Gray900} size={20} />
          <Heading>Timeline</Heading>
        </Box>
        <Box flex={{alignItems: 'center', gap: 8}}>
          {shown ? (
            <ButtonGroup<HourWindow>
              activeItems={new Set([hourWindow])}
              buttons={[
                {id: '1', label: '1hr'},
                {id: '6', label: '6hr'},
                {id: '12', label: '12hr'},
                {id: '24', label: '24hr'},
              ]}
              onClick={(hrWindow: HourWindow) => setHourWindow(hrWindow)}
            />
          ) : null}
          <Button
            icon={<Icon name={shown ? 'unfold_less' : 'unfold_more'} />}
            onClick={() => setShown((current) => !current)}
          >
            {shown ? 'Hide' : 'Show'}
          </Button>
        </Box>
      </Box>
      {shown ? (
        <QueryfulRunTimeline range={[start, end]} jobs={timelineJobs} hourWindow={hourWindow} />
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
      <Table>
        <thead>
          <tr>
            <th style={{width: '40%'}}>Job</th>
            <th style={{width: '25%'}}>Trigger</th>
            <th style={{width: '35%'}}>Latest run</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {jobs.map(({job, repoAddress, runs, schedules, sensors}) => {
            const jobKey = makeJobKey(repoAddress, job.name);
            const repoAddressString = repoAddressAsString(repoAddress);
            return (
              <tr key={jobKey}>
                <td>
                  <Box
                    flex={{
                      direction: 'row',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                    }}
                  >
                    <Box flex={{direction: 'column', gap: 4}}>
                      <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                        <PipelineReference
                          pipelineName={job.name}
                          isJob={job.isJob}
                          pipelineHrefContext={repoAddress}
                        />
                        {!job.isJob ? <LegacyPipelineTag /> : null}
                      </Box>
                      <Body color={Colors.Gray400} style={{fontFamily: FontFamily.monospace}}>
                        {repoAddressString}
                      </Body>
                    </Box>
                    {runs ? (
                      <Box margin={{top: 4}}>
                        <RunStatusPezList fade runs={runs} repoAddress={repoAddressString} />
                      </Box>
                    ) : null}
                  </Box>
                </td>
                <td>
                  {schedules.length || sensors.length ? (
                    <Box flex={{direction: 'column', alignItems: 'flex-start', gap: 8}}>
                      <ScheduleOrSensorTag
                        schedules={schedules}
                        sensors={sensors}
                        repoAddress={repoAddress}
                      />
                      {schedules.length ? <NextTick schedules={schedules} /> : null}
                    </Box>
                  ) : (
                    <div style={{color: Colors.Gray500}}>None</div>
                  )}
                </td>
                <td>
                  <LastRunSummary run={job.runs[0]} />
                </td>
                <td>
                  <JobMenu job={job} repoAddress={repoAddress} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </Table>
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
      mode
      runId
      status
      ...RunTimeFragment
    }
    modes {
      id
      name
    }
  }

  ${RUN_TIME_FRAGMENT}
`;

const INSTANCE_OVERVIEW_INITIAL_QUERY = gql`
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

const LAST_TEN_RUNS_PER_JOB_QUERY = gql`
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
