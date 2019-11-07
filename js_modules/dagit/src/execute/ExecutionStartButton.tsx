import * as React from "react";
import styled from "styled-components";
import { Icon, Intent, Spinner, Colors } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { WebsocketStatusContext } from "../WebsocketStatus";

interface IExecutionStartButtonProps {
  title: string;
  icon: "repeat" | "play";
  small?: boolean;
  onClick: () => void;
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
  _startButton: React.RefObject<any> = React.createRef();

  state = {
    starting: false
  };

  componentDidMount() {
    this._mounted = true;
    document.addEventListener("keyup", this.onKeyUp);
  }

  componentWillUnmount() {
    this._mounted = false;
    document.removeEventListener("keyup", this.onKeyUp);
  }

  onKeyUp = (e: KeyboardEvent) => {
    if (e.ctrlKey && (e.key === "Enter" || e.key === "Return")) {
      // Check that the start button is present to avoid triggering
      // a start event when dagit is offline.
      if (!this._startButton.current) return;

      // Dispatch the button click, starting execution
      e.preventDefault();
      e.stopPropagation();
      this.onClick();
    }
  };

  onClick = async () => {
    this.setState({ starting: true });
    await this.props.onClick();
    setTimeout(() => {
      if (!this._mounted) return;
      this.setState({ starting: false });
    }, 300);
  };

  render() {
    const style = this.props.small
      ? { height: 24, minWidth: 120, paddingLeft: 15, paddingRight: 15 }
      : {};
    const iconSize = this.props.small ? 12 : 17;

    return (
      <WebsocketStatusContext.Consumer>
        {websocketStatus => {
          if (websocketStatus !== WebSocket.OPEN) {
            return (
              <Wrapper
                role="button"
                style={style}
                state={ExecutionButtonStatus.Disabled}
                title={"The dagit server is offline"}
              >
                <Icon
                  icon={IconNames.OFFLINE}
                  iconSize={iconSize}
                  style={{ textAlign: "center", marginRight: 5 }}
                />
                {this.props.title}
              </Wrapper>
            );
          }

          if (this.state.starting) {
            return (
              <Wrapper
                role="button"
                style={style}
                state={ExecutionButtonStatus.Starting}
                title={"Pipeline execution is in progress..."}
              >
                <div style={{ marginRight: 5 }}>
                  <Spinner intent={Intent.NONE} size={iconSize} />
                </div>
                Starting...
              </Wrapper>
            );
          }

          return (
            <Wrapper
              role="button"
              ref={this._startButton}
              style={style}
              state={ExecutionButtonStatus.Ready}
              title={this.props.title}
              onClick={this.onClick}
            >
              <Icon
                icon={this.props.icon}
                iconSize={iconSize}
                style={{ textAlign: "center", marginRight: 5 }}
              />
              {this.props.title}
            </Wrapper>
          );
        }}
      </WebsocketStatusContext.Consumer>
    );
  }
}

const Wrapper = styled.div<{ state: ExecutionButtonStatus }>`
  min-width: 150px;
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
