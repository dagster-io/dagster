import {Box, Colors, Icon, Tooltip} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {LegacyPipelineTag} from '../pipelines/LegacyPipelineTag';
import {humanCronString} from '../schedules/humanCronString';
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
import {ScheduleAndSensorDialog} from './ScheduleAndSensorDialog';

interface Props {
  selector?: string;
  tab?: string;
  repos: DagsterRepoOption[];
  repoPath?: string;
}

export type LeftNavItemType = {
  name: string;
  isJob: boolean;
  label: React.ReactNode;
  path: string;
  repoAddress: RepoAddress;
  schedules: WorkspaceRepositorySchedule[];
  sensors: WorkspaceRepositorySensor[];
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
    const items: LeftNavItemType[] = [];

    for (const option of repos) {
      const {repository, repositoryLocation} = option;
      const address = buildRepoAddress(repository.name, repositoryLocation.name);
      if (!activeRepoAddresses.has(address)) {
        continue;
      }
      items.push(...getLeftNavItemsForOption(option));
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
        <Icon name="job" />
        <span style={{fontSize: '16px', fontWeight: 600}}>{title}</span>
      </Box>
      <Items style={{height: 'calc(100% - 226px)'}}>
        {jobs.map((job) => {
          const repoString = repoAddressAsString(job.repoAddress);
          return (
            <LeftNavItem
              key={`${job.name}-${repoString}`}
              job={job}
              active={!!(repoPath && repoString === repoPath && selector === job.name)}
            />
          );
        })}
      </Items>
    </>
  );
};

export const getLeftNavItemsForOption = (option: DagsterRepoOption) => {
  const items: LeftNavItemType[] = [];

  const {repository, repositoryLocation} = option;
  const address = buildRepoAddress(repository.name, repositoryLocation.name);

  const {schedules, sensors} = repository;
  for (const pipeline of repository.pipelines) {
    if (isHiddenAssetGroupJob(pipeline.name)) {
      continue;
    }

    const {isJob, name} = pipeline;
    const schedulesForJob = schedules.filter((schedule) => schedule.pipelineName === name);
    const sensorsForJob = sensors.filter((sensor) =>
      sensor.targets?.map((target) => target.pipelineName).includes(name),
    );
    items.push({
      name,
      isJob,
      label: (
        <Label $hasIcon={!!(schedules.length || sensors.length) || !isJob}>
          <TruncatingName data-tooltip={name} data-tooltip-style={LabelTooltipStyles}>
            {name}
          </TruncatingName>
          <div style={{flex: 1}} />
          {isJob ? null : <LegacyPipelineTag />}
        </Label>
      ),
      path: workspacePathFromAddress(address, `/${isJob ? 'jobs' : 'pipelines'}/${name}`),
      repoAddress: address,
      schedules: schedulesForJob,
      sensors: sensorsForJob,
    });
  }

  return items;
};

interface LeftNavItemProps {
  active: boolean;
  job: LeftNavItemType;
}

export const LeftNavItem = React.forwardRef(
  (props: LeftNavItemProps, ref: React.ForwardedRef<HTMLDivElement>) => {
    const {active, job: LeftNavItem} = props;
    const {label, path, repoAddress, schedules, sensors} = LeftNavItem;

    const [showDialog, setShowDialog] = React.useState(false);

    const icon = () => {
      const scheduleCount = schedules.length;
      const sensorCount = sensors.length;

      if (!scheduleCount && !sensorCount) {
        return null;
      }

      const whichIcon = scheduleCount ? 'schedule' : 'sensors';
      const needsDialog = scheduleCount > 1 || sensorCount > 1 || (scheduleCount && sensorCount);

      const status = () => {
        return schedules.some(
          (schedule) => schedule.scheduleState.status === InstigationStatus.RUNNING,
        ) || sensors.some((sensor) => sensor.sensorState.status === InstigationStatus.RUNNING)
          ? InstigationStatus.RUNNING
          : InstigationStatus.STOPPED;
      };

      const tooltipContent = () => {
        if (scheduleCount && sensorCount) {
          const scheduleString = scheduleCount > 1 ? `${scheduleCount} schedules` : '1 schedule';
          const sensorString = sensorCount > 1 ? `${sensorCount} sensors` : '1 sensor';
          return `${scheduleString}, ${sensorString}`;
        }

        if (scheduleCount) {
          return scheduleCount === 1 ? (
            <div>
              Schedule: <strong>{humanCronString(schedules[0].cronSchedule)}</strong>
            </div>
          ) : (
            `${scheduleCount} schedules`
          );
        }

        return sensorCount === 1 ? (
          <div>
            Sensor: <strong>{sensors[0].name}</strong>
          </div>
        ) : (
          `${sensorCount} sensors`
        );
      };

      const link = () => {
        const icon = (
          <Icon
            name={whichIcon}
            color={status() === InstigationStatus.RUNNING ? Colors.Green500 : Colors.Gray600}
          />
        );

        if (needsDialog) {
          return (
            <SensorScheduleDialogButton onClick={() => setShowDialog(true)}>
              {icon}
            </SensorScheduleDialogButton>
          );
        }

        const path = scheduleCount
          ? `/schedules/${schedules[0].name}`
          : `/sensors/${sensors[0].name}`;
        return <Link to={workspacePathFromAddress(repoAddress, path)}>{icon}</Link>;
      };

      return (
        <>
          <IconWithTooltip content={tooltipContent()}>{link()}</IconWithTooltip>
          {needsDialog ? (
            <ScheduleAndSensorDialog
              isOpen={showDialog}
              onClose={() => setShowDialog(false)}
              repoAddress={repoAddress}
              schedules={schedules}
              sensors={sensors}
              showSwitch
            />
          ) : null}
        </>
      );
    };

    return (
      <ItemContainer ref={ref}>
        <Item $active={active} to={path}>
          <div>{label}</div>
        </Item>
        {icon()}
      </ItemContainer>
    );
  },
);

const Label = styled.div<{$hasIcon: boolean}>`
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  align-items: center;
  gap: 8px;
  width: ${({$hasIcon}) => ($hasIcon ? '260px' : '280px')};
`;

const SensorScheduleDialogButton = styled.button`
  background: transparent;
  padding: 0;
  margin: 0;
  border: 0;
  cursor: pointer;

  :focus,
  :active,
  :hover {
    outline: none;
  }
`;

const LabelTooltipStyles = JSON.stringify({
  background: Colors.Gray100,
  filter: `brightness(97%)`,
  color: Colors.Gray900,
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
