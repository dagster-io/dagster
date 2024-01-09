import {
  Box,
  Icon,
  Spinner,
  Tooltip,
  colorAccentGray,
  colorAccentYellow,
} from '@dagster-io/ui-components';
import * as React from 'react';

import {DeploymentStatusContext} from '../instance/DeploymentStatusProvider';

import {WarningTooltip} from './WarningTooltip';

export const DeploymentStatusIcon = React.memo(() => {
  return <CombinedStatusIcon />;
});

const CombinedStatusIcon = React.memo(() => {
  const {codeLocations, daemons} = React.useContext(DeploymentStatusContext);

  if (codeLocations?.type === 'spinner') {
    return (
      <Tooltip content={codeLocations.content} placement="bottom">
        <Spinner purpose="body-text" fillColor={colorAccentGray()} />
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
        <Icon name="warning" color={colorAccentYellow()} />
      </WarningTooltip>
    );
  }

  return <div style={{display: 'none'}}>No errors</div>;
});
