import {Colors, Icon, Tooltip} from '@dagster-io/ui-components';
import {memo, useContext} from 'react';

import {DeploymentStatusContext} from '../instance/DeploymentStatusProvider';

export const InstanceWarningIcon = memo(() => {
  const {daemons} = useContext(DeploymentStatusContext);

  if (!daemons) {
    return null;
  }

  return (
    <Tooltip
      content={daemons.content}
      position="bottom"
      modifiers={{offset: {enabled: true, options: {offset: [0, 28]}}}}
    >
      <Icon name="warning" color={Colors.accentYellow()} />
    </Tooltip>
  );
});
