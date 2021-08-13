import {gql, useQuery} from '@apollo/client';
import {Button, ButtonGroup, Colors, Icon} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';
import styled from 'styled-components/macro';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {InstigationStatus} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {DagsterRepoOption} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {Item, Items} from './RepositoryContentList';
import {NavAssetFragment} from './types/NavAssetFragment';
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

type AssetItem = {
  asset: NavAssetFragment;
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

  const [type, setType] = React.useState<'jobs' | 'assets'>('assets');
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
            const sensor = sensors.find((sensor) => sensor.mode === modeName) || null;
            items.push({
              job: tuple,
              label: (
                <Label $hasIcon={!!(schedule || sensor)}>
                  {name}
                  {modeName !== 'default' ? (
                    <span style={{color: Colors.GRAY3}}>{` : ${modeName}`}</span>
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

  const jobsByJobName: {[jobName: string]: JobItem[]} = React.useMemo(() => {
    const _jobs = {};
    jobs.forEach((job) => {
      const jobName = job.job[0];
      _jobs[jobName] = [...(_jobs[jobName] || []), job];
    });
    return _jobs;
  }, [jobs]);

  const assetDefs = React.useMemo(() => {
    if (
      loading ||
      !data ||
      !data.workspaceOrError ||
      data.workspaceOrError.__typename !== 'Workspace'
    ) {
      return [];
    }
    const {locationEntries} = data.workspaceOrError;
    const assetDefs: AssetItem[] = [];
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

        repo.assetDefinitions.forEach((asset) => {
          const jobs = asset.jobName ? jobsByJobName[asset.jobName] || [] : [];
          const schedule = jobs.find((x) => x.schedule)?.schedule || null;
          const sensor = jobs.find((x) => x.sensor)?.sensor || null;
          assetDefs.push({
            asset,
            label: (
              <Label $hasIcon={!!(schedule || sensor)}>{asset.assetKey.path.join(' > ')}</Label>
            ),
            repoAddress: address,
            schedule,
            sensor,
          });
        });
      }
    }
    assetDefs.sort((a: AssetItem, b: AssetItem) => {
      if (a.asset.id > b.asset.id) {
        return 1;
      }
      if (a.asset.id < b.asset.id) {
        return -1;
      }
      return 0;
    });

    return assetDefs;
  }, [loading, data, activeRepoAddresses, jobsByJobName]);

  if (jobs.length === 0) {
    return <div />;
  }

  return (
    <Items style={{height: 'calc(100% - 226px)'}}>
      {assetDefs.length && jobs.length ? (
        <Box
          flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
          padding={{vertical: 8, horizontal: 12}}
          border={{side: 'bottom', width: 1, color: Colors.DARK_GRAY3}}
        >
          <ItemHeader>{'Assets & Jobs'}</ItemHeader>
          <ButtonGroup>
            <Button
              small={true}
              active={type === 'assets'}
              intent={type === 'assets' ? 'primary' : 'none'}
              icon={<Icon icon="box" iconSize={13} />}
              onClick={() => setType('assets')}
            />
            <Button
              small={true}
              active={type === 'jobs'}
              intent={type === 'jobs' ? 'primary' : 'none'}
              icon={<Icon icon="send-to-graph" iconSize={13} />}
              onClick={() => setType('jobs')}
            />
          </ButtonGroup>
        </Box>
      ) : null}
      {type === 'assets'
        ? assetDefs.map(({asset, repoAddress, label, schedule, sensor}) => (
            <Item
              key={asset.id}
              className={`${
                asset.id === selector && repoPath === repoAddressAsString(repoAddress)
                  ? 'selected'
                  : ''
              }`}
              to={workspacePathFromAddress(repoAddress, `/assets/${encodeURIComponent(asset.id)}`)}
            >
              <Box flex={{justifyContent: 'space-between', alignItems: 'center'}}>
                <div>{label}</div>
                <ItemIcon schedule={schedule} sensor={sensor} />
              </Box>
            </Item>
          ))
        : null}
      {type === 'jobs'
        ? jobs.map((job) => (
            <JobItem
              key={`${job.job[0]}:${job.job[1]}-${repoAddressAsString(job.repoAddress)}`}
              job={job}
              repoPath={repoPath}
              selector={selector}
            />
          ))
        : null}
    </Items>
  );
};

const ItemIcon = ({
  schedule,
  sensor,
}: {
  schedule: NavScheduleFragment | null;
  sensor: NavSensorFragment | null;
}) => {
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
        color={status === InstigationStatus.RUNNING ? Colors.GREEN5 : Colors.DARK_GRAY5}
        style={{display: 'block'}}
      />
    </IconWithTooltip>
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

  return (
    <Item
      key={jobName}
      className={`${jobName === selector && repoPath === jobRepoPath ? 'selected' : ''}`}
      to={workspacePathFromAddress(repoAddress, `/jobs/${jobName}`)}
    >
      <Box flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <div>{label}</div>
        <ItemIcon schedule={schedule} sensor={sensor} />
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

const NAV_ASSET_FRAGMENT = gql`
  fragment NavAssetFragment on AssetDefinition {
    id
    assetKey {
      path
    }
    jobName
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
                assetDefinitions {
                  id
                  ...NavAssetFragment
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
  ${NAV_ASSET_FRAGMENT}
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

const ItemHeader = styled.div`
  font-size: 15px;
  text-overflow: ellipsis;
  overflow: hidden;
  font-weight: bold;
  color: ${Colors.LIGHT_GRAY3} !important;
`;
