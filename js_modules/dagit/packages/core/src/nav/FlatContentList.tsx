import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import styled from 'styled-components/macro';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {InstigationStatus} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';
import {Tooltip} from '../ui/Tooltip';
import {DagsterRepoOption} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {Item, Items} from './RepositoryContentList';
import {NavQuery} from './types/NavQuery';
import {NavScheduleFragment} from './types/NavScheduleFragment';
import {NavSensorFragment} from './types/NavSensorFragment';

interface Props {
  selector?: string;
  tab?: string;
  repos: DagsterRepoOption[];
  repoPath?: string;
}

type JobItem = {
  job: [string, string];
  label: React.ReactNode;
  repoAddress: RepoAddress;
  schedule: NavScheduleFragment | null;
  sensor: NavSensorFragment | null;
};

export const FlatContentList: React.FC<Props> = (props) => {
  const {repoPath, repos, selector} = props;

  const activeRepoAddresses = React.useMemo(() => {
    const addresses = repos.map((repo) =>
      buildRepoAddress(repo.repository.name, repo.repositoryLocation.name),
    );
    return new Set(addresses);
  }, [repos]);

  const {loading, data} = useQuery<NavQuery>(NAV_QUERY);

  const jobs = React.useMemo(() => {
    if (
      loading ||
      !data ||
      !data.workspaceOrError ||
      data.workspaceOrError.__typename !== 'Workspace'
    ) {
      return [];
    }

    const {locationEntries} = data.workspaceOrError;
    const items: JobItem[] = [];

    for (const entry of locationEntries) {
      const location = entry.locationOrLoadError;
      if (location?.__typename !== 'RepositoryLocation') {
        continue;
      }

      for (const repo of location.repositories) {
        const address = buildRepoAddress(repo.name, location.name);
        if (!activeRepoAddresses.has(address)) {
          continue;
        }

        for (const pipeline of repo.pipelines) {
          const {name, modes, schedules, sensors} = pipeline;
          modes.forEach((mode) => {
            const modeName = mode.name;
            const tuple: [string, string] = [name, modeName];
            const schedule = schedules.find((schedule) => schedule.mode === modeName) || null;
            const sensor =
              sensors.find((sensor) =>
                sensor.targets?.some(
                  (target) => target.mode === modeName && target.pipelineName === name,
                ),
              ) || null;
            items.push({
              job: tuple,
              label: (
                <Label $hasIcon={!!(schedule || sensor)}>
                  {name}
                  {modeName !== 'default' ? (
                    <span style={{color: ColorsWIP.Gray400}}>{` : ${modeName}`}</span>
                  ) : null}
                </Label>
              ),
              repoAddress: address,
              schedule,
              sensor,
            });
          });
        }
      }
    }

    return items.sort((a, b) =>
      a.job[0].toLocaleLowerCase().localeCompare(b.job[0].toLocaleLowerCase()),
    );
  }, [loading, data, activeRepoAddresses]);

  if (jobs.length === 0) {
    return <div />;
  }

  return (
    <Items style={{height: 'calc(100% - 226px)'}}>
      {jobs.map((job) => (
        <JobItem
          key={`${job.job[0]}:${job.job[1]}-${repoAddressAsString(job.repoAddress)}`}
          job={job}
          repoPath={repoPath}
          selector={selector}
        />
      ))}
    </Items>
  );
};

interface JobItemProps {
  job: JobItem;
  repoPath?: string;
  selector?: string;
}

const JobItem: React.FC<JobItemProps> = (props) => {
  const {job: jobItem, repoPath, selector} = props;
  const {job, label, repoAddress, schedule, sensor} = jobItem;

  const jobName = `${job[0]}:${job[1]}`;
  const jobRepoPath = repoAddressAsString(repoAddress);

  const icon = () => {
    if (!schedule && !sensor) {
      return null;
    }

    const whichIcon = schedule ? 'schedule' : 'sensors';
    const status = schedule ? schedule?.scheduleState.status : sensor?.sensorState.status;
    const tooltipContent = schedule ? (
      <>
        Schedule: <strong>{schedule.name}</strong>
      </>
    ) : (
      <>
        Sensor: <strong>{sensor?.name}</strong>
      </>
    );

    return (
      <IconWithTooltip content={tooltipContent} inheritDarkTheme={false}>
        <IconWIP
          name={whichIcon}
          color={status === InstigationStatus.RUNNING ? ColorsWIP.Green500 : ColorsWIP.Gray600}
        />
      </IconWithTooltip>
    );
  };

  return (
    <Item
      key={jobName}
      className={`${jobName === selector && repoPath === jobRepoPath ? 'selected' : ''}`}
      to={workspacePathFromAddress(repoAddress, `/jobs/${jobName}`)}
    >
      <Box flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <div>{label}</div>
        {icon()}
      </Box>
    </Item>
  );
};

const NAV_SCHEDULE_FRAGMENT = gql`
  fragment NavScheduleFragment on Schedule {
    id
    mode
    name
    scheduleState {
      id
      status
    }
  }
`;

const NAV_SENSOR_FRAGMENT = gql`
  fragment NavSensorFragment on Sensor {
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
  }
`;

const NAV_QUERY = gql`
  query NavQuery {
    workspaceOrError {
      __typename
      ... on Workspace {
        locationEntries {
          __typename
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
                  modes {
                    id
                    name
                  }
                  schedules {
                    id
                    ...NavScheduleFragment
                  }
                  sensors {
                    id
                    ...NavSensorFragment
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
  ${NAV_SCHEDULE_FRAGMENT}
  ${NAV_SENSOR_FRAGMENT}
`;

const Label = styled.div<{$hasIcon: boolean}>`
  overflow: hidden;
  text-overflow: ellipsis;
  width: ${({$hasIcon}) => ($hasIcon ? '224px' : '256px')};
`;

const IconWithTooltip = styled(Tooltip)`
  .bp3-icon:focus,
  .bp3-icon:active {
    outline: none;
  }
`;
