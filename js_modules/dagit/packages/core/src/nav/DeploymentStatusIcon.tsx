import {Box, Colors, Icon, Spinner, Tooltip} from '@dagster-io/ui';
import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {DeploymentStatusContext} from '../instance/DeploymentStatusProvider';

import {InstanceWarningIcon} from './InstanceWarningIcon';
import {WarningTooltip} from './WarningTooltip';

export const DeploymentStatusIcon = React.memo(() => {
  const {flagNewWorkspace} = useFeatureFlags();
  return flagNewWorkspace ? <CombinedStatusIcon /> : <InstanceWarningIcon />;
});

const CombinedStatusIcon = React.memo(() => {
  const {codeLocations, daemons} = React.useContext(DeploymentStatusContext);

  if (codeLocations?.type === 'spinner') {
    return (
      <Tooltip content={codeLocations.content} placement="bottom">
        <Spinner purpose="body-text" fillColor={Colors.Gray300} />
      </Tooltip>
    );
  }

  const anyWarning = daemons?.type === 'warning' || codeLocations?.type === 'warning';

  if (anyWarning) {
    return (
      <WarningTooltip
        content={
          <Box flex={{direction: 'column', gap: 4}}>
            {daemons?.content}
            {codeLocations?.content}
          </Box>
        }
        position="bottom"
        modifiers={{offset: {enabled: true, options: {offset: [0, 28]}}}}
      >
        <Icon name="warning" color={Colors.Yellow500} />
      </WarningTooltip>
    );
  }

  return null;
});
