import {gql, useLazyQuery, useQuery} from '@apollo/client';
import {
  Box,
  AnchorButton,
  ButtonWIP,
  ButtonGroup,
  ColorsWIP,
  IconWIP,
  MenuItemWIP,
  MenuWIP,
  PageHeader,
  Popover,
  Spinner,
  Table,
  TagWIP,
  Body,
  Heading,
  TextInput,
  FontFamily,
} from '@dagster-io/ui';
import * as React from 'react';
import {Redirect} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {QueryCountdown} from '../app/QueryCountdown';
import {ScheduleOrSensorTag} from '../nav/JobMetadata';
import {LegacyPipelineTag} from '../pipelines/LegacyPipelineTag';
import {PipelineReference} from '../pipelines/PipelineReference';
import {RunStatusIndicator} from '../runs/RunStatusDots';
import {RunStatusPezList} from '../runs/RunStatusPez';
import {
  failedStatuses,
  inProgressStatuses,
  queuedStatuses,
  successStatuses,
} from '../runs/RunStatuses';
import {JobMap, RunTimeline} from '../runs/RunTimeline';
import {RunElapsed, RunTime, RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {RunTimeFragment} from '../runs/types/RunTimeFragment';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {InstigationStatus, RunStatus} from '../types/globalTypes';
import {REPOSITORY_INFO_FRAGMENT} from '../workspace/RepositoryInformation';
import {useRepositoryOptions} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath} from '../workspace/workspacePath';

import {InstanceTabs} from './InstanceTabs';
import {JobMenu} from './JobMenu';
import {NextTick, SCHEDULE_FUTURE_TICKS_FRAGMENT} from './NextTick';
import {StepSummaryForRun} from './StepSummaryForRun';
import {
  InstanceOverviewInitialQuery,
  InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules as Schedule,
  InstanceOverviewInitialQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors as Sensor,
} from './types/InstanceOverviewInitialQuery';
import {LastTenRunsPerJobQuery} from './types/LastTenRunsPerJobQuery';
import {OverviewJobFragment} from './types/OverviewJobFragment';

export const InstanceOverviewPage = () => {
  const {flagInstanceOverview} = useFeatureFlags();

  if (!flagInstanceOverview) {
    return <Redirect to="/instance" />;
  }

  return <OverviewContent />;
};

const intent = (status: RunStatus) => {
  switch (status) {
    case RunStatus.SUCCESS:
      return 'success';
    case RunStatus.CANCELED:
    case RunStatus.CANCELING:
    case RunStatus.FAILURE:
      return 'danger';
    default:
      return 'none';
  }
};

const makeJobKey = (repoAddress: RepoAddress, jobName: string) => {
  return `${jobName}-${repoAddressAsString(repoAddress)}`;
};

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
  hiddenRepos: Set<RepoAddress>;
  searchValue: string;
};

type Action = {type: 'toggle-repo'; repo: RepoAddress} | {type: 'search'; value: string};

const reducer = (state: State, action: Action) => {
  switch (action.type) {
    case 'toggle-repo': {
      const copy = new Set(Array.from(state.hiddenRepos));
      copy.has(action.repo) ? copy.delete(action.repo) : copy.add(action.repo);
      return {...state, hiddenRepos: copy};
    }
    case 'search': {
      return {...state, searchValue: action.value};
    }
    default:
      return state;
  }
};

const initialState: State = {
  hiddenRepos: new Set(),
  searchValue: '',
};

const POLL_INTERVAL = 15 * 1000;

const OverviewContent = () => {
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const {options} = useRepositoryOptions();

  const queryResult = useQuery<InstanceOverviewInitialQuery>(INSTANCE_OVERVIEW_INITIAL_QUERY, {
    fetchPolicy: 'network-only',
    pollInterval: POLL_INTERVAL,
    notifyOnNetworkStatusChange: true,
  });
  const {data, loading} = queryResult;

  const [retrieveLastTenRuns, {data: lastTenRunsData}] = useLazyQuery<LastTenRunsPerJobQuery>(
    LAST_TEN_RUNS_PER_JOB_QUERY,
    {fetchPolicy: 'network-only', pollInterval: POLL_INTERVAL},
  );

  const {hiddenRepos, searchValue} = state;

  React.useEffect(() => {
    retrieveLastTenRuns();
  }, [retrieveLastTenRuns]);

  const optionAddresses = React.useMemo(() => {
    if (!options) {
      return [];
    }
    return options.map((option) => {
      const {repository, repositoryLocation} = option;
      return buildRepoAddress(repository.name, repositoryLocation.name);
    });
  }, [options]);

  const bucketed = React.useMemo(() => {
    const failed = [];
    const inProgress = [];
    const succeeded = [];
    const queued = [];
    const neverRan = [];
    const scheduled = [];

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

    if (data && data?.workspaceOrError.__typename === 'Workspace') {
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

              if (schedules.length) {
                const anyFutureTicks = schedules.some(
                  ({scheduleState, futureTicks}) =>
                    scheduleState.status === InstigationStatus.RUNNING &&
                    futureTicks.results.length > 0,
                );
                if (anyFutureTicks) {
                  scheduled.push({
                    job: pipeline,
                    repoAddress,
                    schedules,
                    sensors,
                  });
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
    scheduled.sort(sortFn);

    return {failed, inProgress, queued, succeeded, neverRan, scheduled};
  }, [data]);

  const filteredJobs = React.useMemo(() => {
    const searchToLower = searchValue.toLocaleLowerCase();
    const filterJobs = (item: JobItem) => {
      const {job, repoAddress} = item;
      const {name} = job;
      return !hiddenRepos.has(repoAddress) && name.toLocaleLowerCase().includes(searchToLower);
    };

    const {failed, inProgress, queued, succeeded, neverRan, scheduled} = bucketed;
    return {
      failed: failed.filter(filterJobs),
      inProgress: inProgress.filter(filterJobs),
      queued: queued.filter(filterJobs),
      succeeded: succeeded.filter(filterJobs),
      neverRan: neverRan.filter(filterJobs),
      scheduled: scheduled.filter(filterJobs),
    };
  }, [bucketed, hiddenRepos, searchValue]);

  const lastTenRunsFlattened = React.useMemo(() => {
    if (!lastTenRunsData) {
      return null;
    }

    const flattened: {[key: string]: RunTimeFragment[]} = {};
    if (lastTenRunsData && lastTenRunsData?.workspaceOrError.__typename === 'Workspace') {
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

  const filteredJobsWithRuns = React.useMemo(() => {
    const appendRuns = (jobItem: JobItem) => {
      const {job, repoAddress} = jobItem;
      const jobKey = makeJobKey(repoAddress, job.name);
      const matchingRuns = lastTenRunsFlattened ? lastTenRunsFlattened[jobKey] : [];
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

  const {scheduled} = filteredJobs;
  const jobMapForTimeline: JobMap = React.useMemo(() => {
    const jobMap = Object.keys(filteredJobsWithRuns).reduce((accum, status) => {
      const jobsForStatus: JobItemWithRuns[] = filteredJobsWithRuns[status];
      const toAppend = {};
      for (const jobItem of jobsForStatus) {
        const {repoAddress, job} = jobItem;
        const jobKey = makeJobKey(repoAddress, job.name);
        toAppend[jobKey] = {
          name: job.name,
          path: workspacePipelinePath({
            repoName: repoAddress.name,
            repoLocation: repoAddress.location,
            pipelineName: job.name,
            isJob: job.isJob,
          }),
          runs: [],
        };
      }
      return {...accum, ...toAppend};
    }, {} as JobMap);

    for (const jobItem of scheduled) {
      const {job, repoAddress} = jobItem;
      const jobKey = makeJobKey(repoAddress, job.name);

      // If there are no runs tracked for this job yet because they're only scheduled,
      // add an entry.
      if (!jobMap.hasOwnProperty(jobKey)) {
        jobMap[jobKey] = {
          name: job.name,
          path: workspacePipelinePath({
            repoName: repoAddress.name,
            repoLocation: repoAddress.location,
            pipelineName: job.name,
            isJob: job.isJob,
          }),
          runs: [],
        };
      }
    }

    return jobMap;
  }, [filteredJobsWithRuns, scheduled]);

  if (!data && loading) {
    return (
      <Box padding={64}>
        <Spinner purpose="page" />
      </Box>
    );
  }

  const repoSelector = () => {
    if (optionAddresses.length > 1) {
      const numVisible = optionAddresses.length - hiddenRepos.size;
      return (
        <Popover
          content={
            <MenuWIP>
              {optionAddresses.map((repoAddress) => {
                const repoString = repoAddressAsString(repoAddress);
                const checked = !state.hiddenRepos.has(repoAddress);
                return (
                  <MenuItemWIP
                    icon={
                      <IconWIP
                        name="check_circle"
                        color={checked ? ColorsWIP.Blue500 : ColorsWIP.Gray200}
                      />
                    }
                    shouldDismissPopover={false}
                    key={repoString}
                    text={repoString}
                    onClick={() => dispatch({type: 'toggle-repo', repo: repoAddress})}
                  />
                );
              })}
            </MenuWIP>
          }
          position="bottom-left"
        >
          <ButtonWIP
            icon={<IconWIP name="folder" />}
            rightIcon={<IconWIP name="expand_more" />}
          >{`${numVisible} of ${optionAddresses.length} repositories`}</ButtonWIP>
        </Popover>
      );
    }
    return null;
  };

  const {failed, inProgress, queued, succeeded, neverRan} = filteredJobsWithRuns;

  return (
    <>
      <PageHeader
        title={<Heading>Instance status</Heading>}
        tabs={<InstanceTabs tab="overview" />}
        right={<QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryResult} />}
      />
      <Box
        padding={{horizontal: 24, top: 16}}
        flex={{direction: 'row', alignItems: 'center', gap: 12, grow: 0}}
      >
        {repoSelector()}
        <TextInput
          icon="search"
          value={searchValue}
          onChange={(e) => dispatch({type: 'search', value: e.target.value})}
          placeholder="Filter by job name…"
          style={{width: '340px'}}
        />
      </Box>
      <RunTimelineSection jobs={jobMapForTimeline} />
      {inProgress.length ? (
        <JobSection
          icon={<IconWIP name="hourglass_bottom" color={ColorsWIP.Blue500} size={24} />}
          heading={
            inProgress.length === 1 ? '1 job in progress' : `${inProgress.length} jobs in progress`
          }
          jobs={inProgress}
        />
      ) : null}
      {failed.length ? (
        <JobSection
          icon={<IconWIP name="error_outline" color={ColorsWIP.Red500} size={24} />}
          heading={failed.length === 1 ? '1 job failed' : `${failed.length} jobs failed`}
          jobs={failed}
        />
      ) : null}
      {queued.length ? (
        <JobSection
          icon={<IconWIP name="checklist" color={ColorsWIP.Gray500} size={24} />}
          heading={queued.length === 1 ? '1 job queued' : `${queued.length} jobs queued`}
          jobs={queued}
        />
      ) : null}
      {succeeded.length ? (
        <JobSection
          icon={<IconWIP name="check_circle" color={ColorsWIP.Green500} size={24} />}
          heading={
            succeeded.length === 1 ? '1 job succeeded' : `${succeeded.length} jobs succeeded`
          }
          jobs={succeeded}
        />
      ) : null}
      {neverRan.length ? (
        <JobSection
          icon={<IconWIP name="history_toggle_off" color={ColorsWIP.Gray900} size={24} />}
          heading={neverRan.length === 1 ? '1 job never ran' : `${neverRan.length} jobs never ran`}
          jobs={neverRan}
        />
      ) : null}
    </>
  );
};

interface RunTimelineSectionProps {
  jobs: JobMap;
}

type HourWindow = '1' | '6' | '12' | '24';
const LOOKAHEAD_HOURS = 1;
const ONE_HOUR = 60 * 60 * 1000;

const RunTimelineSection = (props: RunTimelineSectionProps) => {
  const {jobs} = props;
  const [shown, setShown] = React.useState(true);
  const [hourWindow, setHourWindow] = React.useState<HourWindow>('6');
  const now = Date.now();

  const range: [number, number] = React.useMemo(
    () => [now - Number(hourWindow) * ONE_HOUR, now + LOOKAHEAD_HOURS * ONE_HOUR],
    [hourWindow, now],
  );

  return (
    <>
      <Box
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
        margin={{top: 16}}
        padding={{bottom: 16, horizontal: 24}}
        border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
      >
        <Box flex={{alignItems: 'center', gap: 8}}>
          <IconWIP name="waterfall_chart" color={ColorsWIP.Gray900} size={20} />
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
          <ButtonWIP
            icon={<IconWIP name={shown ? 'unfold_less' : 'unfold_more'} />}
            onClick={() => setShown((current) => !current)}
          >
            {shown ? 'Hide' : 'Show'}
          </ButtonWIP>
        </Box>
      </Box>
      {shown ? <RunTimeline jobs={jobs} range={range} /> : null}
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
                      <Body color={ColorsWIP.Gray400} style={{fontFamily: FontFamily.monospace}}>
                        {repoAddressAsString(repoAddress)}
                      </Body>
                    </Box>
                    {runs ? (
                      <Box margin={{top: 4}}>
                        <RunStatusPezList fade runs={runs} />
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
                    <div style={{color: ColorsWIP.Gray500}}>None</div>
                  )}
                </td>
                <td>
                  <Box
                    flex={{
                      direction: 'row',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                    }}
                  >
                    <Box flex={{direction: 'column', alignItems: 'flex-start', gap: 8}}>
                      <TagWIP intent={intent(job.runs[0].status)}>
                        <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                          <RunStatusIndicator status={job.runs[0].status} size={10} />
                          <RunTime run={job.runs[0]} />
                        </Box>
                      </TagWIP>
                      {failedStatuses.has(job.runs[0].status) ||
                      inProgressStatuses.has(job.runs[0].status) ? (
                        <StepSummaryForRun runId={job.runs[0].id} />
                      ) : null}
                    </Box>
                    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
                      <RunElapsed run={job.runs[0]} />
                      <AnchorButton to={`/instance/runs/${job.runs[0].id}`}>View run</AnchorButton>
                    </Box>
                  </Box>
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
            ... on PythonError {
              ...PythonErrorFragment
            }
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
            ... on PythonError {
              ...PythonErrorFragment
            }
          }
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${RUN_TIME_FRAGMENT}
`;
