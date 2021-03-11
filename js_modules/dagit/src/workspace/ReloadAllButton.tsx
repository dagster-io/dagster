import {Button, Icon} from '@blueprintjs/core';
import * as React from 'react';

import {useReloadWorkspace} from 'src/workspace/useReloadWorkspace';

export const ReloadAllButton = () => {
  const {reloading, onClick} = useReloadWorkspace();

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
