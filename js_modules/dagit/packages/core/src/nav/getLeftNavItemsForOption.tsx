import {Colors} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {LegacyPipelineTag} from '../pipelines/LegacyPipelineTag';
import {DagsterRepoOption} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {LeftNavItemType} from './LeftNavItemType';

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

export const getJobItemsForOption = (option: DagsterRepoOption) => {
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
      leftIcon: 'job',
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

const Label = styled.div<{$hasIcon: boolean}>`
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  align-items: center;
  gap: 8px;
  width: ${({$hasIcon}) => ($hasIcon ? '260px' : '280px')};
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
