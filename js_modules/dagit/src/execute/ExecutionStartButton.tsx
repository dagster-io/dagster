import * as React from "react";
import styled from "styled-components/macro";
import { Button, Icon, Intent, Spinner, Colors } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { WebsocketStatusContext } from "../WebsocketStatus";
import { ShortcutHandler } from "../ShortcutHandler";

interface IExecutionStartButtonProps {
  title: string;
  icon: "repeat" | "play" | "disable" | "send-to";
  tooltip?: string;
  activeText?: string;
  small?: boolean;
  disabled?: boolean;
  shortcutLabel?: string;
  shortcutFilter?: (event: KeyboardEvent) => boolean;
  onClick: () => void;
}

interface IExecutionStartButtonState {
  starting: boolean;
}

export enum ExecutionButtonStatus {
  Ready = "ready",
  Starting = "starting",
  Disabled = "disabled"
}

export default class ExecutionStartButton extends React.Component<
  IExecutionStartButtonProps,
  IExecutionStartButtonState
> {
  _mounted = false;
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
              <ExecutionStartButtonContainer
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
              </ExecutionStartButtonContainer>
            );
          }

          if (this.state.starting) {
            return (
              <ExecutionStartButtonContainer
                role="button"
                id="start-execution"
                style={style}
                state={ExecutionButtonStatus.Starting}
                title={"Pipeline execution is in progress..."}
              >
                <div
                  style={{
                    display: "flex",
                    flexDirection: "row",
                    alignItems: "center"
                  }}
                >
                  <Spinner intent={Intent.NONE} size={iconSize} />
                  <div style={{ marginLeft: 5 }}>
                    {this.props.activeText || "Starting..."}
                  </div>
                </div>
              </ExecutionStartButtonContainer>
            );
          }

          if (this.props.disabled) {
            return (
              <ExecutionStartButtonContainer
                role="button"
                style={style}
                state={ExecutionButtonStatus.Disabled}
                title={this.props.tooltip}
              >
                <Icon
                  icon={this.props.icon}
                  iconSize={iconSize}
                  style={{ textAlign: "center", marginRight: 5 }}
                />
                {this.props.title}
              </ExecutionStartButtonContainer>
            );
          }

          return (
            <ShortcutHandler
              onShortcut={this.onClick}
              shortcutLabel={this.props.shortcutLabel}
              shortcutFilter={this.props.shortcutFilter}
            >
              <ExecutionStartButtonContainer
                role="button"
                ref={this._startButton}
                style={style}
                state={ExecutionButtonStatus.Ready}
                title={this.props.tooltip}
                onClick={this.onClick}
              >
                <Icon
                  icon={this.props.icon}
                  iconSize={iconSize}
                  style={{ textAlign: "center", marginRight: 5 }}
                />
                {this.props.title}
              </ExecutionStartButtonContainer>
            </ShortcutHandler>
          );
        }}
      </WebsocketStatusContext.Consumer>
    );
  }
}

export const ExecutionButton = ({
  children,
  small
}: {
  children: React.ReactNode | null;
  small?: boolean;
}) => (
  <WebsocketStatusContext.Consumer>
    {websocketStatus => {
      const disconnected = websocketStatus !== WebSocket.OPEN;
      const swallowEvent = (e: React.SyntheticEvent) => {
        e.preventDefault();
        e.stopPropagation();
      };
      return (
        <ButtonContainer
          state={
            disconnected
              ? ExecutionButtonStatus.Disabled
              : ExecutionButtonStatus.Ready
          }
          small={small}
          onClick={disconnected ? swallowEvent : undefined}
        >
          {children}
        </ButtonContainer>
      );
    }}
  </WebsocketStatusContext.Consumer>
);

const ButtonContainer = styled(Button)<{
  state: ExecutionButtonStatus;
  small?: boolean;
}>`
  &&& {
    height: ${({ small }) => (small ? "24" : "30")}px;
    border-radius: 3px;
    flex-shrink: 0;
    background: ${({ state }) =>
      ({
        disabled:
          "linear-gradient(to bottom, rgb(145, 145, 145) 30%, rgb(130, 130, 130) 100%);",
        ready:
          "linear-gradient(to bottom, rgb(36, 145, 235) 30%, rgb(27, 112, 187) 100%);",
        starting:
          "linear-gradient(to bottom, rgb(21, 89, 150) 30%, rgb(21, 89, 150) 100%);"
      }[state])};
    border-top: 1px solid rgba(255, 255, 255, 0.25);
    border-bottom: 1px solid rgba(0, 0, 0, 0.25);
    transition: background 200ms linear;
    justify-content: center;
    align-items: center;
    display: inline-flex;
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
        }[state])};
    }

    &:active {
      background-color: ${Colors.GRAY3};
    }

    path.bp3-spinner-head {
      stroke: white;
    }

    .bp3-icon {
      color: ${({ state }) =>
        state === "disabled" ? "rgba(255,255,255,0.5)" : "white"};
    }
    .bp3-button-text {
      display: flex;
      align-items: center;
    }
  }
`;

const ExecutionStartButtonContainer = styled(ButtonContainer)`
  &&& {
    min-width: 150px;
    margin-left: 6px;
    padding: 0 25px;
    min-height: 0;
  }
`;
