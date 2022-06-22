import {Button, DialogBody, DialogFooter, Dialog} from '@dagster-io/ui';
import * as React from 'react';

interface ConfirmationOptions {
  catchOnCancel?: boolean;
  title?: string;
  description?: JSX.Element | string;
}

interface ConfirmationDialogProps extends ConfirmationOptions {
  open: boolean;
  onSubmit: () => void;
  onClose: () => void;
}

const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  open,
  title,
  description,
  onSubmit,
  onClose,
}) => {
  return (
    <Dialog icon={title ? 'info' : undefined} onClose={onClose} title={title} isOpen={open}>
      <DialogBody>{description}</DialogBody>
      <DialogFooter>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={onSubmit} intent="danger">
          Confirm
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

export const CustomConfirmationProvider: React.FC = ({children}) => {
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
