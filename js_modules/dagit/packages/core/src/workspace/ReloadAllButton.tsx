import {Button, Icon} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';

import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';

import {useReloadWorkspace} from './useReloadWorkspace';

export const ReloadAllButton = () => {
  const {reloading, onClick} = useReloadWorkspace();
  const {canReloadWorkspace} = usePermissions();

  if (!canReloadWorkspace) {
    return (
      <Tooltip content={DISABLED_MESSAGE}>
        <Button
          icon={<Icon icon="refresh" iconSize={11} />}
          disabled
          text="Reload all"
          small
          intent="none"
        />
      </Tooltip>
    );
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
