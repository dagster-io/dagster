import {Colors, Icon} from '@dagster-io/ui-components';
import * as React from 'react';

import {WarningTooltip} from './WarningTooltip';
import {DeploymentStatusContext} from '../instance/DeploymentStatusProvider';

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
      <Icon name="warning" color={Colors.accentYellow()} />
    </WarningTooltip>
  );
});
