import {Colors} from '@blueprintjs/core';
import debounce from 'lodash/debounce';
import * as React from 'react';
import styled from 'styled-components/macro';
import {SubscriptionClient} from 'subscriptions-transport-ws';

type WebSocketContextType = {
  connectionParams?: {[key: string]: string};
  websocketURI: string;
  status: number;
};

export const WebSocketContext = React.createContext<WebSocketContextType>({
  status: WebSocket.CONNECTING,
  websocketURI: '',
});

const WS_EVENTS = [
  'connecting',
  'connected',
  'reconnecting',
  'reconnected',
  'disconnected',
  'error',
];

// Delay informing listeners of websocket status change so that we don't thrash.
const DEBOUNCE_TIME = 5000;

interface Props {
  connectionParams?: {[key: string]: string};
  websocketURI: string;
}

export const WebSocketProvider: React.FC<Props> = (props) => {
  const {children, connectionParams, websocketURI} = props;
  const [status, setStatus] = React.useState(WebSocket.CONNECTING);

  const websocketClient = React.useMemo(
    () =>
      new SubscriptionClient(websocketURI, {
        reconnect: true,
        connectionParams,
      }),
    [connectionParams, websocketURI],
  );

  const value = React.useMemo(
    () => ({
      connectionParams,
      status,
      websocketURI,
    }),
    [connectionParams, status, websocketURI],
  );

  const debouncedSetter = React.useMemo(() => debounce(setStatus, DEBOUNCE_TIME), []);

  React.useEffect(() => {
    const unlisteners = WS_EVENTS.map((eventName) =>
      websocketClient.on(eventName, () => debouncedSetter(websocketClient.status)),
    );

    return () => {
      unlisteners.forEach((u) => u());
    };
  }, [debouncedSetter, websocketClient]);

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
};

const Circle = styled.div`
  align-self: center;
  width: 12px;
  height: 12px;
  display: inline-block;
  border-radius: 7px;
  border: 1px solid rgba(255, 255, 255, 0.6);
`;

export const WebSocketStatus: React.FC = (props) => (
  <WebSocketContext.Consumer>
    {({status}) =>
      ({
        [WebSocket.CONNECTING]: (
          <Circle style={{background: Colors.GREEN5}} title="Connecting..." {...props} />
        ),
        [WebSocket.OPEN]: (
          <Circle style={{background: Colors.GREEN3}} title="Connected" {...props} />
        ),
        [WebSocket.CLOSING]: (
          <Circle style={{background: Colors.GRAY3}} title="Closing..." {...props} />
        ),
      }[status] || <Circle style={{background: Colors.GRAY3}} title="Disconnected" {...props} />)
    }
  </WebSocketContext.Consumer>
);
