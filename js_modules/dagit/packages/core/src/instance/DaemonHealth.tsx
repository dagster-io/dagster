import {
  Button,
  ButtonLink,
  Colors,
  DialogBody,
  DialogFooter,
  Dialog,
  Group,
  Tag,
  Trace,
} from '@dagster-io/ui';
import * as React from 'react';

import {DaemonHealthFragment_allDaemonStatuses as DaemonStatus} from './types/DaemonHealthFragment';

interface Props {
  daemon: DaemonStatus;
}

const DaemonHealthTag = (props: Props) => {
  const {daemon} = props;

  if (daemon.healthy) {
    return <Tag intent="success">Running</Tag>;
  }

  if (daemon.required) {
    return <Tag intent="danger">Not running</Tag>;
  }

  return <Tag intent="none">Not enabled</Tag>;
};

type State = {
  shown: boolean;
  page: number;
};

type Action = {type: 'show'} | {type: 'hide'} | {type: 'page'; page: number};

const reducer = (state: State, action: Action) => {
  switch (action.type) {
    case 'show':
      return {shown: true, page: 0};
    case 'hide':
      return {shown: false, page: 0};
    case 'page':
      return {...state, page: action.page};
    default:
      return state;
  }
};

const initialState = {shown: false, page: 0};

export const DaemonHealth = (props: Props) => {
  const {daemon} = props;
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const {shown, page} = state;

  const errors = daemon.lastHeartbeatErrors;
  const errorCount = errors.length;

  const show = () => dispatch({type: 'show'});
  const hide = () => dispatch({type: 'hide'});
  const prev = () => dispatch({type: 'page', page: page === 0 ? errorCount - 1 : page - 1});
  const next = () => dispatch({type: 'page', page: page === errorCount - 1 ? 0 : page + 1});

  const metadata = () => {
    if (errorCount > 0) {
      return (
        <>
          <ButtonLink color={Colors.Link} underline="hover" onClick={show}>
            {errorCount > 1 ? `View errors (${errorCount})` : 'View error'}
          </ButtonLink>
          <Dialog
            isOpen={shown}
            title="Daemon error"
            onClose={hide}
            style={{maxWidth: '80%', minWidth: '70%'}}
          >
            <DialogBody>
              <Group direction="column" spacing={12}>
                {errorCount === 1 ? (
                  <div>
                    <strong>{daemon.daemonType}</strong> daemon logged an error.
                  </div>
                ) : (
                  <div>
                    <strong>{daemon.daemonType}</strong> daemon logged {errorCount} errors.
                  </div>
                )}
                <Trace>
                  <Group direction="column" spacing={12}>
                    <div>{errors[page].message}</div>
                    <div>{errors[page].stack}</div>
                  </Group>
                </Trace>
              </Group>
            </DialogBody>
            <DialogFooter
              left={
                errorCount > 1 ? (
                  <Group direction="row" spacing={12} alignItems="center">
                    <ButtonLink onClick={prev}>&larr; Previous</ButtonLink>
                    <span>{`${page + 1} of ${errorCount}`}</span>
                    <ButtonLink onClick={next}>Next &rarr;</ButtonLink>
                  </Group>
                ) : (
                  <div />
                )
              }
            >
              <Button intent="primary" onClick={hide}>
                OK
              </Button>
            </DialogFooter>
          </Dialog>
        </>
      );
    }

    if (!daemon.healthy) {
      return <div style={{color: Colors.Gray500}}>No recent heartbeat</div>;
    }

    return null;
  };

  return (
    <Group direction="row" spacing={8} alignItems="center">
      <DaemonHealthTag daemon={daemon} />
      {metadata()}
    </Group>
  );
};
