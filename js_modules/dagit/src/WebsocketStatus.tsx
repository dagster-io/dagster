import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';
import {SubscriptionClient} from 'subscriptions-transport-ws';

export const WebsocketStatusContext = React.createContext<number>(WebSocket.CONNECTING);

const WS_EVENTS = [
  'connecting',
  'connected',
  'reconnecting',
  'reconnected',
  'disconnected',
  'error',
];

interface IWebsocketStatusProviderProps {
  websocket: SubscriptionClient;
}

interface IWebsocketStatusProviderState {
  status: number;
}

export class WebsocketStatusProvider extends React.Component<
  IWebsocketStatusProviderProps,
  IWebsocketStatusProviderState
> {
  state = {
    status: WebSocket.CONNECTING,
  };

  private unlisteners: Function[] = [];

  componentDidMount() {
    this.unlisteners = WS_EVENTS.map((eventName) =>
      this.props.websocket.on(eventName, () =>
        this.setState({status: this.props.websocket.status}),
      ),
    );
    this.setState({status: this.props.websocket.status});
  }

  componentWillUnmount() {
    this.unlisteners.forEach((u) => u());
  }

  render() {
    return (
      <WebsocketStatusContext.Provider value={this.state.status}>
        {this.props.children}
      </WebsocketStatusContext.Provider>
    );
  }
}

const Circle = styled.div`
  align-self: center;
  width: 14px;
  height: 14px;
  display: inline-block;
  border-radius: 7px;
  border: 1px solid rgba(255, 255, 255, 0.6);
`;

export const WebsocketStatus: React.FunctionComponent = (props) => (
  <WebsocketStatusContext.Consumer>
    {(status) =>
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
  </WebsocketStatusContext.Consumer>
);
