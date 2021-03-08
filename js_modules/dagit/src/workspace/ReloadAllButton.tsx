import {Button, Icon} from '@blueprintjs/core';
import * as React from 'react';

import {WorkspaceContext} from 'src/workspace/WorkspaceContext';
import {useReloadWorkspace} from 'src/workspace/useReloadWorkspace';

export const ReloadAllButton = () => {
  const {locations} = React.useContext(WorkspaceContext);
  const {reloading, onClick} = useReloadWorkspace();
  if (!locations.length) {
    return null;
  }

  return (
    <Button
      onClick={onClick}
      icon={<Icon icon="refresh" iconSize={11} />}
      loading={reloading}
      text="Reload all"
      small
      intent="none"
    />
  );
};
