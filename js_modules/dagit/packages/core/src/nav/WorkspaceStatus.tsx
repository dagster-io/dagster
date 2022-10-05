import {Colors, Icon, Tooltip, Spinner} from '@dagster-io/ui';
import * as React from 'react';

import {DeploymentStatusContext} from '../instance/DeploymentStatusProvider';

import {WarningTooltip} from './WarningTooltip';

export const WorkspaceStatus: React.FC<{placeholder: boolean}> = React.memo(({placeholder}) => {
  const {codeLocations} = React.useContext(DeploymentStatusContext);

  if (!codeLocations) {
    return placeholder ? <div style={{width: '16px'}} /> : null;
  }

  if (codeLocations.type === 'spinner') {
    return (
      <Tooltip content={codeLocations.content} placement="bottom">
        <Spinner purpose="body-text" fillColor={Colors.Gray300} />
      </Tooltip>
    );
  }

  return (
    <WarningTooltip
      content={codeLocations.content}
      position="bottom"
      modifiers={{offset: {enabled: true, options: {offset: [0, 28]}}}}
    >
      <Icon name="warning" color={Colors.Yellow500} />
    </WarningTooltip>
  );
});
