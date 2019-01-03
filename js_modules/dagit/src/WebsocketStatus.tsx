import * as React from "react";
import { SubscriptionClient } from "subscriptions-transport-ws";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";

const WS_EVENTS = [
  "connecting",
  "connected",
  "reconnecting",
  "reconnected",
  "disconnected",
  "error"
];

export const WebsocketContext = React.createContext<SubscriptionClient | null>(
  null
);

interface IWebsocketStateDisplayProps {
  websocket: SubscriptionClient;
}

interface IWebsocketStateDisplayState {
  status: number;
}

class WebsocketStateDisplay extends React.Component<
  IWebsocketStateDisplayProps,
  IWebsocketStateDisplayState
> {
  state = {
    status: WebSocket.CONNECTING
  };

  private unlisteners: Function[] = [];

  componentDidMount() {
    this.unlisteners = WS_EVENTS.map(eventName =>
      this.props.websocket.on(eventName, () =>
        this.setState({ status: this.props.websocket.status })
      )
    );
    this.setState({ status: this.props.websocket.status });
  }

  componentWillUnmount() {
    this.unlisteners.forEach(u => u());
  }

  render() {
    switch (this.state.status) {
      case WebSocket.CONNECTING:
        return (
          <Circle style={{ background: Colors.GREEN5 }} title="Connecting..." />
        );
      case WebSocket.OPEN:
        return (
          <Circle style={{ background: Colors.GREEN3 }} title="Connected" />
        );
      case WebSocket.CLOSING:
        return (
          <Circle style={{ background: Colors.GRAY3 }} title="Closing..." />
        );
      default:
        return (
          <Circle style={{ background: Colors.GRAY3 }} title="Disconnected" />
        );
    }
  }
}

const Circle = styled.div`
  align-self: center;
  width: 10px;
  height: 10px;
  display: inline-block;
  border-radius: 5px;
  margin: 5px;
`;

export default () => {
  return (
    <WebsocketContext.Consumer>
      {websocket =>
        websocket && <WebsocketStateDisplay websocket={websocket} />
      }
    </WebsocketContext.Consumer>
  );
};
