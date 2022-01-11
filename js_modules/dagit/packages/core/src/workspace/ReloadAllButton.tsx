import {ButtonWIP, IconWIP, Tooltip} from '@dagster-io/ui';
import * as React from 'react';

import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';

import {useReloadWorkspace} from './useReloadWorkspace';

export const ReloadAllButton = () => {
  const {reloading, onClick} = useReloadWorkspace();
  const {canReloadWorkspace} = usePermissions();

  if (!canReloadWorkspace) {
    return (
      <Tooltip content={DISABLED_MESSAGE}>
        <ButtonWIP icon={<IconWIP name="refresh" />} disabled intent="none">
          Reload all
        </ButtonWIP>
      </Tooltip>
    );
  }

  return (
    <ButtonWIP
      onClick={onClick}
      icon={<IconWIP name="refresh" />}
      loading={reloading}
      intent="none"
    >
      Reload all
    </ButtonWIP>
  );
};
