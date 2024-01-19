import {Icon, Tooltip, Spinner, Colors} from '@dagster-io/ui-components';
import * as React from 'react';

import {DeploymentStatusContext} from '../instance/DeploymentStatusProvider';

import {WarningTooltip} from './WarningTooltip';

export const WorkspaceStatus = React.memo(({placeholder}: {placeholder: boolean}) => {
  const {codeLocations} = React.useContext(DeploymentStatusContext);

  if (!codeLocations) {
    return placeholder ? <div style={{width: '16px'}} /> : null;
  }

  if (codeLocations.type === 'spinner') {
    return (
      <Tooltip content={codeLocations.content} placement="bottom">
        <Spinner purpose="body-text" fillColor={Colors.accentGray()} />
      </Tooltip>
    );
  }

  return (
    <WarningTooltip
      content={codeLocations.content}
      position="bottom"
      modifiers={{offset: {enabled: true, options: {offset: [0, 28]}}}}
    >
      <Icon name="warning" color={Colors.accentYellow()} />
    </WarningTooltip>
  );
});
