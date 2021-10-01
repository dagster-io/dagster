import {Button} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';

import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';
import {IconWIP} from '../ui/Icon';

import {useReloadWorkspace} from './useReloadWorkspace';

export const ReloadAllButton = () => {
  const {reloading, onClick} = useReloadWorkspace();
  const {canReloadWorkspace} = usePermissions();

  if (!canReloadWorkspace) {
    return (
      <Tooltip content={DISABLED_MESSAGE}>
        <Button icon={<IconWIP name="refresh" />} disabled text="Reload all" small intent="none" />
      </Tooltip>
    );
  }

  return (
    <Button
      onClick={onClick}
      icon={<IconWIP name="refresh" />}
      loading={reloading}
      text="Reload all"
      small
      intent="none"
    />
  );
};
