import {Box, Button, Dialog, DialogBody, DialogFooter, Icon, Mono} from '@dagster-io/ui-components';
import {ReactNode} from 'react';

import styles from './css/UIComponentMutationFailedDialog.module.css';
import {UIComponentMutationContext} from './uiComponentMutationContext';

interface Props {
  isOpen: boolean;
  ctx: UIComponentMutationContext | null;
  errorMessage: string;
  isReverting: boolean;
  onRevert: () => void;
  onDismiss: () => void;
}

const SUMMARY: Record<UIComponentMutationContext['kind'], (componentId: string) => ReactNode> = {
  add: (id) => (
    <>
      Adding <Mono>{id}</Mono> caused the code location to fail to load. You can revert the change
      to restore the location, or dismiss to investigate.
    </>
  ),
  edit: (id) => (
    <>
      Editing <Mono>{id}</Mono> caused the code location to fail to load. You can revert the change
      to restore the location, or dismiss to investigate.
    </>
  ),
  delete: (id) => (
    <>
      Deleting <Mono>{id}</Mono> caused the code location to fail to load. You can revert the change
      to restore the location, or dismiss to investigate.
    </>
  ),
};

const REVERT_LABEL: Record<UIComponentMutationContext['kind'], string> = {
  add: 'Delete added component',
  edit: 'Restore previous attributes',
  delete: 'Recreate deleted component',
};

export const UIComponentMutationFailedDialog = ({
  isOpen,
  ctx,
  errorMessage,
  isReverting,
  onRevert,
  onDismiss,
}: Props) => {
  return (
    <Dialog
      isOpen={isOpen}
      title="Code location failed to load"
      icon="info"
      onClose={() => !isReverting && onDismiss()}
      style={{width: '50vw', minWidth: 500, maxWidth: 900}}
    >
      <DialogBody>
        <Box flex={{direction: 'column', gap: 12}}>
          {ctx ? <span>{SUMMARY[ctx.kind](ctx.componentId)}</span> : null}
          <div className={styles.errorBlock}>{errorMessage}</div>
        </Box>
      </DialogBody>
      <DialogFooter topBorder>
        <Button onClick={onDismiss} disabled={isReverting}>
          Dismiss
        </Button>
        {ctx ? (
          <Button
            intent="danger"
            icon={<Icon name="settings_backup_restore" />}
            onClick={onRevert}
            disabled={isReverting}
          >
            {isReverting ? 'Reverting…' : REVERT_LABEL[ctx.kind]}
          </Button>
        ) : null}
      </DialogFooter>
    </Dialog>
  );
};
