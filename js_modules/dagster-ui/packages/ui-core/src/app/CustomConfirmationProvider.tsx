import * as React from 'react';

import {Button, Dialog, DialogBody, DialogFooter} from '@dagster-io/ui-components';

interface ConfirmationOptions {
  catchOnCancel?: boolean;
  title?: string;
  description?: React.ReactNode;
  icon?: ConfirmationDialogProps['icon'];
  intent?: ConfirmationDialogProps['intent'];
  buttonText?: React.ReactNode;
}

interface ConfirmationDialogProps extends ConfirmationOptions {
  open: boolean;
  icon?: React.ComponentProps<typeof Dialog>['icon'];
  intent?: React.ComponentProps<typeof Button>['intent'];
  onSubmit: () => void;
  onClose: () => void;
}

const ConfirmationDialog = ({
  open,
  icon,
  title,
  intent = 'danger',
  buttonText = 'Confirm',
  description,
  onSubmit,
  onClose,
}: ConfirmationDialogProps) => {
  return (
    <Dialog icon={title ? icon ?? 'info' : icon} onClose={onClose} title={title} isOpen={open}>
      <DialogBody>{description}</DialogBody>
      <DialogFooter topBorder>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={onSubmit} intent={intent}>
          {buttonText}
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const CustomConfirmationContext = React.createContext<
  (options: ConfirmationOptions) => Promise<void>
>(Promise.reject);

export const useConfirmation = () => React.useContext(CustomConfirmationContext);

const REMOVAL_DELAY = 500;

export const CustomConfirmationProvider = ({children}: {children: React.ReactNode}) => {
  const [mounted, setMounted] = React.useState(false);
  const [confirmationState, setConfirmationState] = React.useState<ConfirmationOptions | null>(
    null,
  );

  const awaitingPromiseRef = React.useRef<{
    resolve: () => void;
    reject: () => void;
  }>();

  // When a confirmation is set, allow the Dialog to be mounted. When it is cleared,
  // remove the Dialog from the tree so that its root node doesn't linger in the DOM
  // and cause subsequent z-index bugs.
  React.useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    if (!!confirmationState) {
      setMounted(true);
    } else {
      timer = setTimeout(() => setMounted(false), REMOVAL_DELAY);
    }
    return () => timer && clearTimeout(timer);
  }, [confirmationState]);

  const openConfirmation = (options: ConfirmationOptions) => {
    setConfirmationState(options);
    return new Promise<void>((resolve, reject) => {
      awaitingPromiseRef.current = {resolve, reject};
    });
  };

  const handleClose = () => {
    if (confirmationState?.catchOnCancel && awaitingPromiseRef.current) {
      awaitingPromiseRef.current.reject();
    }

    setConfirmationState(null);
  };

  const handleSubmit = () => {
    if (awaitingPromiseRef.current) {
      awaitingPromiseRef.current.resolve();
    }

    setConfirmationState(null);
  };

  return (
    <>
      <CustomConfirmationContext.Provider value={openConfirmation}>
        {children}
      </CustomConfirmationContext.Provider>
      {mounted ? (
        <ConfirmationDialog
          open={!!confirmationState}
          onSubmit={handleSubmit}
          onClose={handleClose}
          {...confirmationState}
        />
      ) : null}
    </>
  );
};
