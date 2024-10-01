import {Button, Dialog, DialogBody, DialogFooter, Icon, Tooltip} from '@dagster-io/ui-components';
import {useEffect, useState} from 'react';

import {RepositoryLocationErrorDialog} from './RepositoryLocationErrorDialog';
import {useUnscopedPermissions} from '../app/Permissions';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {
  reloadFnForWorkspace,
  useRepositoryLocationReload,
} from '../nav/useRepositoryLocationReload';

interface Props {
  icon?: React.ComponentProps<typeof Button>['icon'];
  label?: React.ReactNode;
}

export const ReloadAllButton = (props: Props) => {
  const {icon = <Icon name="reload_definitions" />, label = 'Reload all'} = props;
  const {
    permissions: {canReloadWorkspace},
    disabledReasons,
  } = useUnscopedPermissions();
  const {reloading, tryReload, error, errorLocationId} = useRepositoryLocationReload({
    scope: 'workspace',
    reloadFn: reloadFnForWorkspace,
  });

  const [isOpen, setIsOpen] = useState(!!error);
  useEffect(() => setIsOpen(!!error), [error]);

  if (!canReloadWorkspace) {
    return (
      <Tooltip content={disabledReasons.canReloadWorkspace}>
        <Button outlined icon={icon} disabled>
          {label}
        </Button>
      </Tooltip>
    );
  }

  return (
    <>
      <Button outlined onClick={tryReload} icon={icon} loading={reloading}>
        {label}
      </Button>
      {errorLocationId ? (
        <RepositoryLocationErrorDialog
          error={error}
          location={errorLocationId}
          reloading={reloading}
          onTryReload={tryReload}
          onDismiss={() => setIsOpen(false)}
          isOpen={isOpen}
        />
      ) : (
        <Dialog
          icon="error"
          title="Reload error"
          canEscapeKeyClose={false}
          canOutsideClickClose={false}
          style={{width: '90%'}}
          isOpen={isOpen}
        >
          <DialogBody>{error && <PythonErrorInfo error={error} />}</DialogBody>
          <DialogFooter>
            <Button onClick={() => setIsOpen(false)}>Dismiss</Button>
          </DialogFooter>
        </Dialog>
      )}
    </>
  );
};
