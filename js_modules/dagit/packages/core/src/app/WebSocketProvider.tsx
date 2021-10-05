import debounce from 'lodash/debounce';
import * as React from 'react';
import styled from 'styled-components/macro';
import {SubscriptionClient} from 'subscriptions-transport-ws';

import {ColorsWIP} from '../ui/Colors';

type Availability = 'attempting-to-connect' | 'unavailable' | 'available';

export type WebSocketContextType = {
  availability: Availability;
  status: number;
  websocketClient?: SubscriptionClient;
};

export const WebSocketContext = React.createContext<WebSocketContextType>({
  availability: 'attempting-to-connect',
  status: WebSocket.CONNECTING,
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
  websocketClient: SubscriptionClient;
}

export const WebSocketProvider: React.FC<Props> = (props) => {
  const {children, websocketClient} = props;
  const [status, setStatus] = React.useState(WebSocket.CONNECTING);
  const [availability, setAvailability] = React.useState<Availability>('attempting-to-connect');

  const value = React.useMemo(
    () => ({
      availability,
      status,
      websocketClient,
    }),
    [availability, status, websocketClient],
  );

  const debouncedSetter = React.useMemo(() => debounce(setStatus, DEBOUNCE_TIME), []);

  React.useEffect(() => {
    const availabilityListeners = [
      websocketClient.onConnected(() => setAndUnlisten('available')),
      websocketClient.onError(() => setAndUnlisten('unavailable')),
    ];

    const unlisten = () => availabilityListeners.forEach((u) => u());
    const setAndUnlisten = (value: Availability) => {
      unlisten();
      setAvailability(value);
    };

    return () => {
      unlisten();
    };
  }, [websocketClient]);

  React.useEffect(() => {
    const statusListeners = WS_EVENTS.map((eventName) =>
      websocketClient.on(eventName, () => {
        debouncedSetter(websocketClient.status);
      }),
    );

    return () => {
      statusListeners.forEach((u) => u());
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
          <Circle style={{background: ColorsWIP.Green500}} title="Connecting..." {...props} />
        ),
        [WebSocket.OPEN]: (
          <Circle style={{background: ColorsWIP.Green700}} title="Connected" {...props} />
        ),
        [WebSocket.CLOSING]: (
          <Circle style={{background: ColorsWIP.Gray400}} title="Closing..." {...props} />
        ),
      }[status] || (
        <Circle style={{background: ColorsWIP.Gray400}} title="Disconnected" {...props} />
      ))
    }
  </WebSocketContext.Consumer>
);
