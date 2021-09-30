import * as React from 'react';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment';
import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
import {DialogBody, DialogFooter, DialogWIP} from '../ui/Dialog';

interface Props {
  location: string;
  isOpen: boolean;
  error: PythonErrorFragment | {message: string} | null;
  reloading: boolean;
  onDismiss: () => void;
  onTryReload: () => void;
}

export const RepositoryLocationErrorDialog: React.FC<Props> = (props) => {
  const {isOpen, error, location, reloading, onTryReload, onDismiss} = props;
  return (
    <DialogWIP
      icon="error"
      title="Repository location error"
      isOpen={isOpen}
      canEscapeKeyClose={false}
      canOutsideClickClose={false}
      style={{width: '90%'}}
    >
      <DialogBody>
        <ErrorContents location={location} error={error} />
      </DialogBody>
      <DialogFooter>
        <ButtonWIP onClick={onTryReload} loading={reloading} intent="primary">
          Reload again
        </ButtonWIP>
        <ButtonWIP onClick={onDismiss}>Dismiss</ButtonWIP>
      </DialogFooter>
    </DialogWIP>
  );
};

export const RepositoryLocationNonBlockingErrorDialog: React.FC<Props> = (props) => {
  const {isOpen, error, location, reloading, onTryReload, onDismiss} = props;
  return (
    <DialogWIP
      icon="error"
      title="Repository location error"
      isOpen={isOpen}
      style={{width: '90%'}}
      onClose={onDismiss}
    >
      <DialogBody>
        <ErrorContents location={location} error={error} />
      </DialogBody>
      <DialogFooter>
        <ButtonWIP onClick={onTryReload} loading={reloading} intent="primary">
          Reload
        </ButtonWIP>
        <ButtonWIP onClick={onDismiss}>Close</ButtonWIP>
      </DialogFooter>
    </DialogWIP>
  );
};

const ErrorContents: React.FC<{
  location: string;
  error: PythonErrorFragment | {message: string} | null;
}> = ({location, error}) => (
  <>
    <Box margin={{bottom: 12}}>
      Error loading <strong>{location}</strong>. Try reloading the repository location after
      resolving the issue.
    </Box>
    {error ? <PythonErrorInfo error={error} /> : null}
  </>
);
