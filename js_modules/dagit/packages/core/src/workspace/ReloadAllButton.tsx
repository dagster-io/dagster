import {Button, Dialog, DialogBody, DialogFooter, Icon, Tooltip} from '@dagster-io/ui';
import * as React from 'react';

import {usePermissions} from '../app/Permissions';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {
  reloadFnForWorkspace,
  useRepositoryLocationReload,
} from '../nav/useRepositoryLocationReload';

import {RepositoryLocationErrorDialog} from './RepositoryLocationErrorDialog';

export const ReloadAllButton: React.FC<{label?: string}> = ({label = 'Reload all'}) => {
  const {canReloadWorkspace} = usePermissions();
  const {reloading, tryReload, error, errorLocationId} = useRepositoryLocationReload({
    scope: 'workspace',
    reloadFn: reloadFnForWorkspace,
  });

  const [isOpen, setIsOpen] = React.useState(!!error);
  React.useEffect(() => setIsOpen(!!error), [error]);

  if (!canReloadWorkspace.enabled) {
    return (
      <Tooltip content={canReloadWorkspace.disabledReason}>
        <Button icon={<Icon name="refresh" />} disabled intent="none">
          {label}
        </Button>
      </Tooltip>
    );
  }

  return (
    <>
      <Button onClick={tryReload} icon={<Icon name="refresh" />} loading={reloading} intent="none">
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
