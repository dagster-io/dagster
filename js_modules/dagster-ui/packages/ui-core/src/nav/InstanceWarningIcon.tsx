import {Colors, Icon} from '@dagster-io/ui-components';
import {memo, useContext} from 'react';

import {WarningTooltip} from './WarningTooltip';
import {DeploymentStatusContext} from '../instance/DeploymentStatusProvider';

export const InstanceWarningIcon = memo(() => {
  const {daemons} = useContext(DeploymentStatusContext);

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
