import {Box, Colors, Icon, Spinner, Tooltip} from '@dagster-io/ui';
import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';

import {InstanceWarningIcon, useDeploymentStatus} from './InstanceWarningIcon';
import {WarningTooltip} from './WarningTooltip';
import {useWorkspaceStatus} from './WorkspaceStatus';

export const DeploymentStatusIcon = React.memo(() => {
  const {flagNewWorkspace} = useFeatureFlags();
  return flagNewWorkspace ? <CombinedStatusIcon /> : <InstanceWarningIcon />;
});

const CombinedStatusIcon = React.memo(() => {
  const deploymentStatus = useDeploymentStatus();
  const workspaceStatus = useWorkspaceStatus();

  if (workspaceStatus?.type === 'spinner') {
    return (
      <Tooltip content={workspaceStatus.content} placement="bottom">
        <Spinner purpose="body-text" fillColor={Colors.Gray300} />
      </Tooltip>
    );
  }

  const anyWarning = deploymentStatus?.type === 'warning' || workspaceStatus?.type === 'warning';

  if (anyWarning) {
    return (
      <WarningTooltip
        content={
          <Box flex={{direction: 'column', gap: 4}}>
            {deploymentStatus?.content}
            {workspaceStatus?.content}
          </Box>
        }
        position="bottom"
        modifiers={{offset: {enabled: true, options: {offset: [0, 28]}}}}
      >
        <Icon name="warning" color={Colors.Yellow500} />
      </WarningTooltip>
    );
  }

  return <div style={{width: '16px'}} />;
});
