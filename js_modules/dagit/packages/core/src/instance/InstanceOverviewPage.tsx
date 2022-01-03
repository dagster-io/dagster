import {gql, useLazyQuery, useQuery} from '@apollo/client';
import * as React from 'react';
import {Redirect} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {RUN_METADATA_FRAGMENT, ScheduleOrSensorTag} from '../nav/JobMetadata';
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
import {RunElapsed, RunTime, RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {RunStatus} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';
import {MenuItemWIP, MenuWIP} from '../ui/Menu';
import {PageHeader} from '../ui/PageHeader';
import {Popover} from '../ui/Popover';
import {Spinner} from '../ui/Spinner';
import {Table} from '../ui/Table';
import {TagWIP} from '../ui/TagWIP';
import {Body, Heading} from '../ui/Text';
import {TextInput} from '../ui/TextInput';
import {FontFamily} from '../ui/styles';
import {REPOSITORY_INFO_FRAGMENT} from '../workspace/RepositoryInformation';
import {useRepositoryOptions} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

import {InstanceTabs} from './InstanceTabs';
import {NextTick, SCHEDULE_FUTURE_TICKS_FRAGMENT} from './NextTick';
import {InstanceOverviewInitialQuery} from './types/InstanceOverviewInitialQuery';
import {LastTenRunsPerJobQuery} from './types/LastTenRunsPerJobQuery';
import {OverviewJobFragment} from './types/OverviewJobFragment';
import {RunStatusFragment} from './types/RunStatusFragment';

export const InstanceOverviewPage = () => {
  const {flagInstanceOverview} = useFeatureFlags();

  if (!flagInstanceOverview) {
    return <Redirect to="/instance" />;
  }

  return (
    <>
      <PageHeader
        title={<Heading>Instance status</Heading>}
        tabs={<InstanceTabs tab="overview" />}
      />
      <OverviewContent />
    </>
  );
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
};

type JobItemWithRuns = JobItem & {
  runs: RunStatusFragment[];
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

const OverviewContent = () => {
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const {options} = useRepositoryOptions();
  const {data, loading} = useQuery<InstanceOverviewInitialQuery>(INSTANCE_OVERVIEW_INITIAL_QUERY);
  const [retrieveLastTenRuns, {data: lastTenRunsData}] = useLazyQuery<LastTenRunsPerJobQuery>(
    LAST_TEN_RUNS_PER_JOB_QUERY,
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

    const sortFn = (a: JobItem, b: JobItem) => {
      const aRun = a.job.runs[0] || null;
      const bRun = b.job.runs[0] || null;

      if (aRun?.stats.__typename === 'RunStatsSnapshot') {
        if (bRun?.stats.__typename === 'RunStatsSnapshot') {
          const aStart = aRun.stats.startTime;
          const bStart = bRun.stats.startTime;
          if (aStart) {
            return bStart ? bStart - aStart : -1;
          }
          return 1;
        }
      } else if (bRun?.stats.__typename === 'RunStatsSnapshot') {
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
              if (runs.length) {
                const {status} = runs[0];
                const item = {
                  job: pipeline,
                  repoAddress: buildRepoAddress(
                    repository.name,
                    locationEntry.locationOrLoadError.name,
                  ),
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
    const filterJobs = (item: JobItem) => {
      const {job, repoAddress} = item;
      const {name} = job;
      return !hiddenRepos.has(repoAddress) && name.toLocaleLowerCase().includes(searchToLower);
    };

    const {failed, inProgress, queued, succeeded, neverRan} = bucketed;
    return {
      failed: failed.filter(filterJobs),
      inProgress: inProgress.filter(filterJobs),
      queued: queued.filter(filterJobs),
      succeeded: succeeded.filter(filterJobs),
      neverRan: neverRan.filter(filterJobs),
    };
  }, [bucketed, hiddenRepos, searchValue]);

  const lastTenRunsFlattened = React.useMemo(() => {
    if (!lastTenRunsData) {
      return null;
    }

    const flattened = {};
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

  if (loading) {
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
            <th style={{width: '30%'}}>Trigger</th>
            <th style={{width: '30%'}}>Latest run</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {jobs.map(({job, repoAddress, runs}) => {
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
                  {job.schedules.length || job.sensors.length ? (
                    <Box flex={{direction: 'column', alignItems: 'flex-start', gap: 8}}>
                      <ScheduleOrSensorTag job={job} repoAddress={repoAddress} />
                      {job.schedules.length ? <NextTick schedules={job.schedules} /> : null}
                    </Box>
                  ) : (
                    <div style={{color: ColorsWIP.Gray500}}>None</div>
                  )}
                </td>
                <td>
                  <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                    <TagWIP intent={intent(job.runs[0].status)}>
                      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                        <RunStatusIndicator status={job.runs[0].status} size={10} />
                        <RunTime run={job.runs[0]} />
                      </Box>
                    </TagWIP>
                    <RunElapsed run={job.runs[0]} />
                  </Box>
                </td>
                <td>
                  <ButtonWIP icon={<IconWIP name="expand_more" />} />
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
      ...RunMetadataFragment
      ...RunTimeFragment
    }
    modes {
      id
      name
    }
    schedules {
      id
      mode
      name
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
        mode
        pipelineName
      }
      sensorState {
        id
        status
      }
      ...SensorSwitchFragment
    }
  }

  ${SCHEDULE_SWITCH_FRAGMENT}
  ${SCHEDULE_FUTURE_TICKS_FRAGMENT}
  ${SENSOR_SWITCH_FRAGMENT}
  ${RUN_METADATA_FRAGMENT}
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
                    ...RunStatusFragment
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

  fragment RunStatusFragment on Run {
    id
    runId
    status
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
