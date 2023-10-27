import {Box, Button, DialogBody, DialogFooter, Dialog} from '@dagster-io/ui-components';
import * as React from 'react';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';

interface Props {
  location: string;
  isOpen: boolean;
  error: PythonErrorFragment | {message: string} | null;
  reloading: boolean;
  onDismiss: () => void;
  onTryReload: () => void;
}

export const RepositoryLocationErrorDialog = (props: Props) => {
  const {isOpen, error, location, reloading, onTryReload, onDismiss} = props;
  return (
    <Dialog
      icon="error"
      title="Code location error"
      isOpen={isOpen}
      canEscapeKeyClose={false}
      canOutsideClickClose={false}
      style={{width: '90%'}}
    >
      <DialogBody>
        <ErrorContents location={location} error={error} />
      </DialogBody>
      <DialogFooter>
        <Button onClick={onTryReload} loading={reloading} intent="primary">
          Reload again
        </Button>
        <Button onClick={onDismiss}>Dismiss</Button>
      </DialogFooter>
    </Dialog>
  );
};

export const RepositoryLocationNonBlockingErrorDialog = (props: Props) => {
  const {isOpen, error, location, reloading, onTryReload, onDismiss} = props;
  return (
    <Dialog
      icon="error"
      title="Code location error"
      isOpen={isOpen}
      style={{width: '90%'}}
      onClose={onDismiss}
    >
      <DialogBody>
        <ErrorContents location={location} error={error} />
      </DialogBody>
      <DialogFooter>
        <Button onClick={onTryReload} loading={reloading} intent="primary">
          Reload
        </Button>
        <Button onClick={onDismiss}>Close</Button>
      </DialogFooter>
    </Dialog>
  );
};

const ErrorContents = ({
  location,
  error,
}: {
  location: string;
  error: PythonErrorFragment | {message: string} | null;
}) => (
  <>
    <Box margin={{bottom: 12}}>
      Error loading <strong>{location}</strong>. Try reloading the code location after resolving the
      issue.
    </Box>
    {error ? <PythonErrorInfo error={error} /> : null}
  </>
);
