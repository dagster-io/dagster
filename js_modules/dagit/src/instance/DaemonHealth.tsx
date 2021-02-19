import {Button, Classes, Colors, Dialog, Tag} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {DaemonHealthFragment_allDaemonStatuses as DaemonStatus} from 'src/instance/types/DaemonHealthFragment';
import {Box} from 'src/ui/Box';
import {ButtonLink} from 'src/ui/ButtonLink';
import {Group} from 'src/ui/Group';
import {Trace} from 'src/ui/Trace';

interface Props {
  daemon: DaemonStatus;
}

const DaemonHealthTag = (props: Props) => {
  const {daemon} = props;

  if (daemon.healthy) {
    return (
      <HoverTag minimal intent="success">
        Running
      </HoverTag>
    );
  }

  if (daemon.required) {
    return (
      <HoverTag minimal intent="danger">
        Not running
      </HoverTag>
    );
  }

  return (
    <HoverTag minimal intent="none">
      Not enabled
    </HoverTag>
  );
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
          <ButtonLink color={Colors.BLUE2} underline="hover" onClick={show}>
            {errorCount > 1 ? `View errors (${errorCount})` : 'View error'}
          </ButtonLink>
          <Dialog
            isOpen={shown}
            title="Daemon error"
            onClose={hide}
            style={{maxWidth: '80%', minWidth: '70%'}}
          >
            <div className={Classes.DIALOG_BODY}>
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
            </div>
            <div className={Classes.DIALOG_FOOTER}>
              <Box flex={{alignItems: 'center', justifyContent: 'space-between'}}>
                {errorCount > 1 ? (
                  <Group direction="row" spacing={12} alignItems="center">
                    <ButtonLink onClick={prev}>&larr; Previous</ButtonLink>
                    <span>{`${page + 1} of ${errorCount}`}</span>
                    <ButtonLink onClick={next}>Next &rarr;</ButtonLink>
                  </Group>
                ) : (
                  <div />
                )}
                <Button onClick={hide}>OK</Button>
              </Box>
            </div>
          </Dialog>
        </>
      );
    }

    if (!daemon.healthy) {
      return <div style={{color: Colors.GRAY2}}>No recent heartbeat</div>;
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

const HoverTag = styled(Tag)`
  cursor: default;
  user-select: none;
`;
