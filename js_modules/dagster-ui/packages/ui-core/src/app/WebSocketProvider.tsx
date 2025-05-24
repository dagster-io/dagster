import {Colors} from '@dagster-io/ui-components';
import debounce from 'lodash/debounce';
import * as React from 'react';
import styles from './WebSocketProvider.module.css';

import {useFeatureFlags} from './Flags';
import {SubscriptionClient} from 'subscriptions-transport-ws';

type Availability = 'attempting-to-connect' | 'unavailable' | 'available';

export type WebSocketContextType = {
  availability: Availability;
  status: number;
  disabled?: boolean;
  websocketClient?: SubscriptionClient;
};

export const WebSocketContext = React.createContext<WebSocketContextType>({
  availability: 'attempting-to-connect',
  status: WebSocket.CONNECTING,
  disabled: false,
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

// The amount of time we're willing to wait for the server to ack the WS connection
// before we give up and call WebSockets unavailable. This can occur when the connection
// just hangs but never closes or errors.
const TIME_TO_WAIT_FOR_ACK = 10000;

interface Props {
  children: React.ReactNode;
  websocketClient: SubscriptionClient;
}

export const WebSocketProvider = (props: Props) => {
  const {children, websocketClient} = props;
  const [status, setStatus] = React.useState(websocketClient.status);
  const {flagDisableWebsockets: disabled} = useFeatureFlags();

  const [availability, setAvailability] = React.useState<Availability>(
    websocketClient.status === WebSocket.OPEN
      ? 'available'
      : websocketClient.status === WebSocket.CLOSED
        ? 'unavailable'
        : 'attempting-to-connect',
  );

  const value = React.useMemo(
    () => ({
      availability,
      status,
      websocketClient,
      disabled,
    }),
    [availability, disabled, status, websocketClient],
  );

  const debouncedSetter = React.useMemo(() => debounce(setStatus, DEBOUNCE_TIME), []);

  React.useEffect(() => {
    // Note: In Firefox, we sometimes see websockets closed with the error message
    // "The connection to wss://... was interrupted while the page was loading"
    // The client reconnects, but we need to continue listening for state changes
    // after "onError" below to realize that websockets are in fact supported.
    const availabilityListeners = [
      websocketClient.onConnected(() => setFinalAvailability('available')),
      websocketClient.onReconnected(() => setFinalAvailability('available')),
      websocketClient.onError(() => setAvailability('unavailable')),
    ];

    const unlisten = () => {
      availabilityListeners.forEach((u) => u());
    };

    const setFinalAvailability = (value: Availability) => {
      unlisten();
      setAvailability(value);
    };

    return unlisten;
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

  // Wait a little while for the server to ack the WebSocket connection. If it never
  // acks, never closes, and never errors, we shouldn't keep the app waiting to connect
  // forever. Instead, set WebSocket availability as `unavailable` and let use cases
  // fall back to non-WS implementations.
  React.useEffect(() => {
    let timeout: ReturnType<typeof setTimeout> | null = null;
    if (availability === 'attempting-to-connect') {
      timeout = setTimeout(() => {
        console.log('[WebSockets] Timed out waiting for WS connection.');
        setAvailability('unavailable');
      }, TIME_TO_WAIT_FOR_ACK);
    }

    return () => {
      if (timeout) {
        clearTimeout(timeout);
      }
    };
  }, [availability]);

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
};

export const WebSocketStatus = (props: React.ComponentProps<'div'>) => (
  <WebSocketContext.Consumer>
    {({status}) =>
      ({
        [WebSocket.CONNECTING]: (
          <div
            className={styles.circle}
            style={{background: Colors.accentLime()}}
            title="Connecting..."
            {...props}
          />
        ),
        [WebSocket.OPEN]: (
          <div
            className={styles.circle}
            style={{background: Colors.accentGreen()}}
            title="Connected"
            {...props}
          />
        ),
        [WebSocket.CLOSING]: (
          <div
            className={styles.circle}
            style={{background: Colors.accentGray()}}
            title="Closing..."
            {...props}
          />
        ),
      })[status] || (
        <div
          className={styles.circle}
          style={{background: Colors.accentGray()}}
          title="Disconnected"
          {...props}
        />
      )
    }
  </WebSocketContext.Consumer>
);
