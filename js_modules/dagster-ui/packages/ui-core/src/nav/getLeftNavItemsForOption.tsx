import {Colors} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {LeftNavItemType} from './LeftNavItemType';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {LegacyPipelineTag} from '../pipelines/LegacyPipelineTag';
import {DagsterRepoOption} from '../workspace/WorkspaceContext/util';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../workspace/workspacePath';

export const getAssetGroupItemsForOption = (option: DagsterRepoOption) => {
  const items: LeftNavItemType[] = [];

  const {repository, repositoryLocation} = option;
  const address = buildRepoAddress(repository.name, repositoryLocation.name);

  for (const {groupName} of repository.assetGroups) {
    items.push({
      name: groupName || '',
      leftIcon: 'asset_group',
      isJob: false,
      schedules: [],
      sensors: [],
      repoAddress: address,
      path: workspacePathFromAddress(address, `/asset-groups/${groupName}`),
      label: (
        <Label $hasIcon={false}>
          <TruncatingName data-tooltip={groupName} data-tooltip-style={LabelTooltipStyles}>
            {groupName}
          </TruncatingName>
        </Label>
      ),
    });
  }

  return items.sort((a, b) => a.name.localeCompare(b.name));
};

export const getTopLevelResourceDetailsItemsForOption = (option: DagsterRepoOption) => {
  const items: LeftNavItemType[] = [];

  const {repository, repositoryLocation} = option;
  const address = buildRepoAddress(repository.name, repositoryLocation.name);

  for (const resource of repository.allTopLevelResourceDetails) {
    items.push({
      name: resource.name,
      leftIcon: 'resource',
      isJob: false,
      schedules: [],
      sensors: [],
      repoAddress: address,
      path: workspacePathFromAddress(address, `/resources/${resource.name}`),
      label: (
        <Label $hasIcon={false}>
          <TruncatingName data-tooltip={resource.name} data-tooltip-style={LabelTooltipStyles}>
            {resource.name}
          </TruncatingName>
        </Label>
      ),
    });
  }

  return items;
};

export const getJobItemsForOption = (option: DagsterRepoOption) => {
  const items: LeftNavItemType[] = [];

  const {repository, repositoryLocation} = option;
  const address = buildRepoAddress(repository.name, repositoryLocation.name);

  const {schedules, sensors} = repository;
  const someInRepoHasIcon = !!(schedules.length || sensors.length);

  for (const pipeline of repository.pipelines) {
    if (isHiddenAssetGroupJob(pipeline.name)) {
      continue;
    }

    const {isJob, name} = pipeline;
    const schedulesForJob = schedules.filter((schedule) => schedule.pipelineName === name);
    const sensorsForJob = sensors.filter(
      (sensor) => sensor.targets?.map((target) => target.pipelineName).includes(name),
    );

    items.push({
      name,
      isJob,
      leftIcon: 'job',
      label: (
        <Label $hasIcon={someInRepoHasIcon}>
          <TruncatedTextWithFullTextOnHover text={name} />
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

const Label = styled.div<{$hasIcon: boolean}>`
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  align-items: center;
  gap: 8px;
  margin-right: ${({$hasIcon}) => ($hasIcon === true ? '20px' : '0px')};
  white-space: nowrap;
`;

export const LabelTooltipStyles = JSON.stringify({
  background: Colors.backgroundLight(),
  filter: `brightness(97%)`,
  color: Colors.textDefault(),
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

export const TruncatedTextWithFullTextOnHover = React.forwardRef(
  (
    {
      text,
      tooltipStyle,
      tooltipText,
      ...rest
    }:
      | {text: string; tooltipStyle?: string; tooltipText?: null}
      | {text: React.ReactNode; tooltipStyle?: string; tooltipText: string},
    ref: React.ForwardedRef<HTMLDivElement>,
  ) => (
    <TruncatingName
      data-tooltip={tooltipText ?? text}
      data-tooltip-style={tooltipStyle ?? LabelTooltipStyles}
      ref={ref}
      {...rest}
    >
      {text}
    </TruncatingName>
  ),
);
