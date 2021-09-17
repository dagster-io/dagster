import * as React from 'react';

import {WebSocketContext} from './WebSocketProvider';

export const useWebsocketAvailability = () => {
  const {websocketClient} = React.useContext(WebSocketContext);
  const [status, setStatus] = React.useState<'attempting-to-connect' | 'error' | 'success'>(
    'attempting-to-connect',
  );

  // Determine whether WebSockets are available at all. If not, fall back to a version
  // that uses a polling query.
  React.useEffect(() => {
    if (!websocketClient) {
      return;
    }

    let cleanup = () => {};

    if (websocketClient.status === WebSocket.OPEN) {
      setStatus('success');
    } else if (websocketClient.status === WebSocket.CLOSED) {
      setStatus('error');
    } else {
      const errUnlisten = websocketClient.onError(() => setStatus('error'));
      const connUnlisten = websocketClient.onConnected(() => setStatus('success'));
      cleanup = () => {
        errUnlisten();
        connUnlisten();
      };
    }

    return () => {
      cleanup();
    };
  }, [websocketClient]);

  return status;
};
