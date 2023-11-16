import {Icon, colorAccentYellow} from '@dagster-io/ui-components';
import * as React from 'react';

import {DeploymentStatusContext} from '../instance/DeploymentStatusProvider';

import {WarningTooltip} from './WarningTooltip';

export const InstanceWarningIcon = React.memo(() => {
  const {daemons} = React.useContext(DeploymentStatusContext);

  if (!daemons) {
    return null;
  }

  return (
    <WarningTooltip
      content={daemons.content}
      position="bottom"
      modifiers={{offset: {enabled: true, options: {offset: [0, 28]}}}}
    >
      <Icon name="warning" color={colorAccentYellow()} />
    </WarningTooltip>
  );
});
