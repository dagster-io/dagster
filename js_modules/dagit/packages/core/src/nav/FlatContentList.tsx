import {gql, useQuery} from '@apollo/client';
import {Colors, Icon} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';
import styled from 'styled-components/macro';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {JobStatus} from '../types/globalTypes';
import {Box} from '../ui/Box';
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
            items.push({
              job: tuple,
              label: (
                <span>
                  {name}
                  {modeName !== 'default' ? (
                    <span style={{color: Colors.GRAY3}}>{` : ${modeName}`}</span>
                  ) : null}
                </span>
              ),
              repoAddress: address,
              schedule: schedules.find((schedule) => schedule.mode === modeName) || null,
              sensor: sensors.find((sensor) => sensor.mode === modeName) || null,
            });
          });
        }
      }
    }

    return items;
  }, [loading, data, activeRepoAddresses]);

  const content = () => {
    if (jobs.length === 0) {
      return <div />;
    }

    return (
      <Items style={{height: 'calc(100% - 128px)'}}>
        {jobs.map((job) => (
          <JobItem
            key={`${job.job[0]}:${job.job[1]}`}
            job={job}
            repoPath={repoPath}
            selector={selector}
          />
        ))}
      </Items>
    );
  };

  return <div>{content()}</div>;
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

    const whichIcon = schedule ? 'time' : 'automatic-updates';
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
        <Icon
          icon={whichIcon}
          iconSize={12}
          color={status === JobStatus.RUNNING ? Colors.GREEN5 : Colors.DARK_GRAY5}
          style={{display: 'block'}}
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
    mode
    name
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

const IconWithTooltip = styled(Tooltip)`
  .bp3-icon:focus,
  .bp3-icon:active {
    outline: none;
  }
`;
