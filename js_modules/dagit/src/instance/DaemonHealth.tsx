import {Button, Classes, Colors, Dialog, Tag} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {DaemonHealthFragment_allDaemonStatuses as DaemonStatus} from 'src/instance/types/DaemonHealthFragment';
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

export const DaemonHealth = (props: Props) => {
  const {daemon} = props;
  const [showDialog, setShowDialog] = React.useState(false);

  const metadata = () => {
    if (daemon.lastHeartbeatErrors.length > 0) {
      return (
        <>
          <ButtonLink color={Colors.BLUE2} underline="hover" onClick={() => setShowDialog(true)}>
            View error
          </ButtonLink>
          <Dialog
            isOpen={showDialog}
            title="Daemon error"
            onClose={() => setShowDialog(false)}
            style={{maxWidth: '80%', minWidth: '50%'}}
          >
            <div className={Classes.DIALOG_BODY}>
              <Group direction="column" spacing={12}>
                <div>
                  Error running daemon type <strong>{daemon.daemonType}</strong>. Try restarting the
                  daemon after resolving the issue.
                </div>
                <Trace>
                  <Group direction="column" spacing={12}>
                    <div>{daemon.lastHeartbeatErrors[0].message}</div>
                    <div>{daemon.lastHeartbeatErrors[0].stack}</div>
                  </Group>
                </Trace>
              </Group>
            </div>
            <div className={Classes.DIALOG_FOOTER}>
              <div className={Classes.DIALOG_FOOTER_ACTIONS}>
                <Button onClick={() => setShowDialog(false)}>OK</Button>
              </div>
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
