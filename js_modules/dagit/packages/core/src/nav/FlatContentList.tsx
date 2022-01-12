import {Box, ColorsWIP, IconWIP, Tooltip} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {LegacyPipelineTag} from '../pipelines/LegacyPipelineTag';
import {InstigationStatus} from '../types/globalTypes';
import {
  DagsterRepoOption,
  WorkspaceRepositorySchedule,
  WorkspaceRepositorySensor,
} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {Item, Items} from './RepositoryContentList';

interface Props {
  selector?: string;
  tab?: string;
  repos: DagsterRepoOption[];
  repoPath?: string;
}

type JobItem = {
  name: string;
  isJob: boolean;
  label: React.ReactNode;
  repoAddress: RepoAddress;
  schedule: WorkspaceRepositorySchedule | null;
  sensor: WorkspaceRepositorySensor | null;
};

export const FlatContentList: React.FC<Props> = (props) => {
  const {repoPath, repos, selector} = props;

  const activeRepoAddresses = React.useMemo(() => {
    const addresses = repos.map((repo) =>
      buildRepoAddress(repo.repository.name, repo.repositoryLocation.name),
    );
    return new Set(addresses);
  }, [repos]);

  const jobs = React.useMemo(() => {
    const items: JobItem[] = [];

    for (const {repository, repositoryLocation} of repos) {
      const address = buildRepoAddress(repository.name, repositoryLocation.name);
      if (!activeRepoAddresses.has(address)) {
        continue;
      }

      const {schedules, sensors} = repository;
      for (const pipeline of repository.pipelines) {
        const {isJob, name} = pipeline;
        const schedule = schedules.find((schedule) => schedule.pipelineName === name) || null;
        const sensor =
          sensors.find((sensor) =>
            sensor.targets?.map((target) => target.pipelineName).includes(name),
          ) || null;
        items.push({
          name,
          isJob,
          label: (
            <Label $hasIcon={!!(schedule || sensor) || !isJob}>
              <TruncatingName data-tooltip={name} data-tooltip-style={LabelTooltipStyles}>
                {name}
              </TruncatingName>
              <div style={{flex: 1}} />
              {isJob ? null : <LegacyPipelineTag />}
            </Label>
          ),
          repoAddress: address,
          schedule,
          sensor,
        });
      }
    }

    return items.sort((a, b) =>
      a.name.toLocaleLowerCase().localeCompare(b.name.toLocaleLowerCase()),
    );
  }, [repos, activeRepoAddresses]);

  const title = jobs.some((j) => !j.isJob) ? 'Jobs and pipelines' : 'Jobs';

  return (
    <>
      <Box
        flex={{direction: 'row', alignItems: 'center', gap: 8}}
        padding={{horizontal: 24, bottom: 12}}
      >
        <IconWIP name="job" />
        <span style={{fontSize: '16px', fontWeight: 600}}>{title}</span>
      </Box>
      <Items style={{height: 'calc(100% - 226px)'}}>
        {jobs.map((job) => (
          <JobItem
            key={`${job.name}-${repoAddressAsString(job.repoAddress)}`}
            job={job}
            repoPath={repoPath}
            selector={selector}
          />
        ))}
      </Items>
    </>
  );
};

interface JobItemProps {
  job: JobItem;
  repoPath?: string;
  selector?: string;
}

const JobItem: React.FC<JobItemProps> = (props) => {
  const {job: jobItem, repoPath, selector} = props;
  const {name, isJob, label, repoAddress, schedule, sensor} = jobItem;

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
    const path = schedule ? `/schedules/${schedule.name}` : `/sensors/${sensor?.name}`;

    return (
      <IconWithTooltip content={tooltipContent}>
        <Link to={workspacePathFromAddress(repoAddress, path)}>
          <IconWIP
            name={whichIcon}
            color={status === InstigationStatus.RUNNING ? ColorsWIP.Green500 : ColorsWIP.Gray600}
          />
        </Link>
      </IconWithTooltip>
    );
  };

  return (
    <ItemContainer>
      <Item
        key={name}
        className={`${name === selector && repoPath === jobRepoPath ? 'selected' : ''}`}
        to={workspacePathFromAddress(repoAddress, `/${isJob ? 'jobs' : 'pipelines'}/${name}`)}
      >
        <div>{label}</div>
      </Item>
      {icon()}
    </ItemContainer>
  );
};

const Label = styled.div<{$hasIcon: boolean}>`
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  align-items: center;
  gap: 8px;
  width: ${({$hasIcon}) => ($hasIcon ? '260px' : '280px')};
`;

const LabelTooltipStyles = JSON.stringify({
  background: ColorsWIP.Gray100,
  filter: `brightness(97%)`,
  color: ColorsWIP.Gray900,
  border: 'none',
  borderRadius: 7,
  overflow: 'hidden',
  fontSize: 14,
  padding: '5px 10px',
  transform: 'translate(-10px,-5px)',
} as React.CSSProperties);

const TruncatingName = styled.div`
  flex-shrink: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const IconWithTooltip = styled(Tooltip)`
  position: absolute;
  right: 8px;
  top: 6px;

  & a:focus,
  & a:active {
    outline: none;
  }
`;

const ItemContainer = styled.div`
  position: relative;
`;
