import {Button, Icon, Tooltip} from '@dagster-io/ui';
import * as React from 'react';

import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';

import {useReloadWorkspace} from './useReloadWorkspace';

export const ReloadAllButton = () => {
  const {reloading, onClick} = useReloadWorkspace();
  const {canReloadWorkspace} = usePermissions();

  if (!canReloadWorkspace) {
    return (
      <Tooltip content={DISABLED_MESSAGE}>
        <Button icon={<Icon name="refresh" />} disabled intent="none">
          Reload all
        </Button>
      </Tooltip>
    );
  }

  return (
    <Button onClick={onClick} icon={<Icon name="refresh" />} loading={reloading} intent="none">
      Reload all
    </Button>
  );
};
