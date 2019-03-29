import * as React from "react";
import styled from "styled-components";
import { Icon, Intent, Spinner, Colors } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { WebsocketStatusContext } from "../WebsocketStatus";

interface IExecutionStartButtonProps {
  onClick: (event: React.MouseEvent<HTMLDivElement, MouseEvent>) => void;
}

interface IExecutionStartButtonState {
  starting: boolean;
}

enum ExecutionButtonStatus {
  Ready = "ready",
  Starting = "starting",
  Disabled = "disabled"
}

export default class ExecutionStartButton extends React.Component<
  IExecutionStartButtonProps,
  IExecutionStartButtonState
> {
  _mounted: boolean = false;

  state = {
    starting: false
  };

  componentDidMount() {
    this._mounted = true;
  }

  componentWillUnmount() {
    this._mounted = false;
  }

  onClick = async (event: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    this.setState({ starting: true });
    await this.props.onClick(event);
    setTimeout(() => {
      if (!this._mounted) return;
      this.setState({ starting: false });
    }, 300);
  };

  render() {
    return (
      <WebsocketStatusContext.Consumer>
        {websocketStatus => {
          console.log("rendering start button");
          if (websocketStatus !== WebSocket.OPEN) {
            return (
              <Wrapper
                role="button"
                state={ExecutionButtonStatus.Disabled}
                title={"The dagit server is offline"}
              >
                <div style={{ marginRight: 5 }}>
                  <Icon icon={IconNames.OFFLINE} iconSize={17} />
                </div>
                Start Execution
              </Wrapper>
            );
          }

          if (this.state.starting) {
            return (
              <Wrapper
                role="button"
                state={ExecutionButtonStatus.Starting}
                title={"Pipeline execution is in progress..."}
              >
                <div style={{ marginRight: 5 }}>
                  <Spinner intent={Intent.NONE} size={17} />
                </div>
                Starting...
              </Wrapper>
            );
          }

          return (
            <Wrapper
              role="button"
              state={ExecutionButtonStatus.Ready}
              title={"Start pipeline execution"}
              onClick={this.onClick}
            >
              <Icon icon={IconNames.PLAY} iconSize={17} />
              Start Execution
            </Wrapper>
          );
        }}
      </WebsocketStatusContext.Consumer>
    );
  }
}

const Wrapper = styled.div<{ state: ExecutionButtonStatus }>`
  width: 150px;
  height: 30px;
  border-radius: 3px;
  margin-left: 6px;
  flex-shrink: 0;
  background: ${({ state }) =>
    ({
      disabled:
        "linear-gradient(to bottom, rgb(145, 145, 145) 30%, rgb(130, 130, 130) 100%);",
      ready:
        "linear-gradient(to bottom, rgb(36, 145, 235) 30%, rgb(27, 112, 187) 100%);",
      starting:
        "linear-gradient(to bottom, rgb(21, 89, 150) 30%, rgb(21, 89, 150) 100%);"
    }[state])}
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
  border-top: 1px solid rgba(255,255,255,0.25);
  border-bottom: 1px solid rgba(0,0,0,0.25);
  transition: background 200ms linear;
  justify-content: center;
  align-items: center;
  display: flex;
  color: ${({ state }) =>
    state === "disabled" ? "rgba(255,255,255,0.5)" : "white"};
  cursor: ${({ state }) => (state !== "ready" ? "normal" : "pointer")};
  z-index: 2;

  &:hover {
    background: ${({ state }) =>
      ({
        disabled:
          "linear-gradient(to bottom, rgb(145, 145, 145) 30%, rgb(130, 130, 130) 100%);",
        ready:
          "linear-gradient(to bottom, rgb(27, 112, 187) 30%, rgb(21, 89, 150) 100%);",
        starting:
          "linear-gradient(to bottom, rgb(21, 89, 150) 30%, rgb(21, 89, 150) 100%);"
      }[state])}
  }

  &:active {
    background-color: ${Colors.GRAY3};
  }

  path.bp3-spinner-head {
    stroke: white;
  }
`;
