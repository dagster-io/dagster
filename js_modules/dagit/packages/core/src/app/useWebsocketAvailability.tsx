import * as React from 'react';

import {WebSocketContext} from './WebSocketProvider';

export const useWebsocketAvailability = () => {
  const {websocketURI} = React.useContext(WebSocketContext);
  const [status, setStatus] = React.useState<'attempting-to-connect' | 'error' | 'success'>(
    'attempting-to-connect',
  );

  // Determine whether WebSockets are available at all. If not, fall back to a version
  // that uses a polling query.
  React.useEffect(() => {
    const ws = new WebSocket(websocketURI, 'graphql-ws');
    ws.addEventListener('error', () => setStatus('error'));
    ws.addEventListener('open', () => {
      setStatus('success');
      ws.close();
    });

    return () => ws.close();
  }, [websocketURI]);

  return status;
};
