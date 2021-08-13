import {Button, Classes, Dialog} from '@blueprintjs/core';
import * as React from 'react';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment';
import {Box} from '../ui/Box';

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
    <Dialog
      isOpen={isOpen}
      title="Repository location error"
      canEscapeKeyClose={false}
      canOutsideClickClose={false}
      style={{width: '90%'}}
    >
      <ErrorContents location={location} error={error} />
      <div className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          <Button onClick={onTryReload} loading={reloading} intent="primary">
            Reload again
          </Button>
          <Button onClick={onDismiss}>Dismiss</Button>
        </div>
      </div>
    </Dialog>
  );
};

export const RepositoryLocationNonBlockingErrorDialog: React.FC<Props> = (props) => {
  const {isOpen, error, location, reloading, onTryReload, onDismiss} = props;
  return (
    <Dialog isOpen={isOpen} title="Repository location error" style={{width: '90%'}}>
      <ErrorContents location={location} error={error} />
      <div className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          <Button onClick={onTryReload} loading={reloading} intent="primary">
            Reload
          </Button>
          <Button onClick={onDismiss}>Close</Button>
        </div>
      </div>
    </Dialog>
  );
};

const ErrorContents: React.FC<{
  location: string;
  error: PythonErrorFragment | {message: string} | null;
}> = ({location, error}) => (
  <div className={Classes.DIALOG_BODY}>
    <Box margin={{bottom: 12}}>
      Error loading <strong>{location}</strong>. Try reloading the repository location after
      resolving the issue.
    </Box>
    {error ? <PythonErrorInfo error={error} /> : null}
  </div>
);
