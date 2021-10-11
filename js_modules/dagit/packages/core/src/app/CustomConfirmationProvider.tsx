import * as React from 'react';

import {ButtonWIP} from '../ui/Button';
import {DialogBody, DialogFooter, DialogWIP} from '../ui/Dialog';

interface ConfirmationOptions {
  catchOnCancel?: boolean;
  title?: string;
  description?: JSX.Element | string;
  confirmIntent?: 'primary' | 'danger';
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
  confirmIntent,
  onSubmit,
  onClose,
}) => {
  return (
    <DialogWIP icon={title ? 'info' : undefined} onClose={onClose} title={title} isOpen={open}>
      <DialogBody>{description}</DialogBody>
      <DialogFooter>
        <ButtonWIP onClick={onClose}>Cancel</ButtonWIP>
        <ButtonWIP onClick={onSubmit} intent={confirmIntent}>
          Confirm
        </ButtonWIP>
      </DialogFooter>
    </DialogWIP>
  );
};

const CustomConfirmationContext = React.createContext<
  (options: ConfirmationOptions) => Promise<void>
>(Promise.reject);

export const useConfirmation = () => React.useContext(CustomConfirmationContext);

export const CustomConfirmationProvider: React.FunctionComponent = ({children}) => {
  const [confirmationState, setConfirmationState] = React.useState<ConfirmationOptions | null>(
    null,
  );

  const awaitingPromiseRef = React.useRef<{
    resolve: () => void;
    reject: () => void;
  }>();

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

      <ConfirmationDialog
        open={Boolean(confirmationState)}
        onSubmit={handleSubmit}
        onClose={handleClose}
        {...confirmationState}
      />
    </>
  );
};
