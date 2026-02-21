import {Colors, Icon, Spinner, Tooltip} from '@dagster-io/ui-components';
import {memo, useContext} from 'react';

import {DeploymentStatusContext} from '../instance/DeploymentStatusProvider';

export const WorkspaceStatus = memo(({placeholder}: {placeholder: boolean}) => {
  const {codeLocations} = useContext(DeploymentStatusContext);

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
    <Tooltip
      content={codeLocations.content}
      position="bottom"
      modifiers={{offset: {enabled: true, options: {offset: [0, 28]}}}}
    >
      <Icon name="warning" color={Colors.accentYellow()} />
    </Tooltip>
  );
});
