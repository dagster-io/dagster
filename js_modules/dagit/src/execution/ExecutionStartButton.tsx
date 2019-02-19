import * as React from "react";
import styled from "styled-components";
import { Icon, Intent, Spinner, Colors } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { WebsocketStatusContext } from "../WebsocketStatus";

interface IExecutionStartButtonProps {
  executing: boolean;
  onClick: (event: React.MouseEvent<HTMLDivElement, MouseEvent>) => void;
}

export default function ExecutionStartButton(
  props: IExecutionStartButtonProps
) {
  return (
    <WebsocketStatusContext.Consumer>
      {websocketStatus => {
        if (props.executing) {
          return (
            <Wrapper
              role="button"
              title={"Pipeline execution is in progress..."}
            >
              <div style={{marginRight: 5}}><Spinner intent={Intent.NONE} size={17} /></div>
              Running...
            </Wrapper>
          );
        }

        if (websocketStatus !== WebSocket.OPEN) {
          return (
            <Wrapper
              role="button"
              disabled={true}
              title={"Dagit is disconnected"}
            >
              <Icon icon={IconNames.OFFLINE} iconSize={17} />
            Start Execution
            </Wrapper>
          );
        }

        return (
          <Wrapper
            role="button"
            title={"Start pipeline execution"}
            onClick={props.onClick}
          >
            <Icon icon={IconNames.PLAY} iconSize={17} />
            Start Execution
          </Wrapper>
        );
      }}
    </WebsocketStatusContext.Consumer>
  );
}

const Wrapper = styled.div<{ disabled?: boolean }>`
  width: 150px;
  height: 30px;
  border-radius: 3px;
  margin-left: 6px;
  flex-shrink: 0;
  background: ${({ disabled }) =>
    disabled
      ? "linear-gradient(to bottom, rgb(145, 145, 145) 30%, rgb(130, 130, 130) 100%);"
      : "linear-gradient(to bottom, rgb(36, 145, 235) 30%, rgb(27, 112, 187) 100%);"}
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
  border-top: 1px solid rgba(255,255,255,0.25);
  border-bottom: 1px solid rgba(0,0,0,0.25);
  transition: background 200ms linear;
  justify-content: center;
  align-items: center;
  display: flex;
  color: ${({ disabled }) => (disabled ? "rgba(255,255,255,0.5)" : "white")};;
  cursor: ${({ disabled }) => (disabled ? "normal" : "pointer")};
  z-index: 2;

  &:hover {
    background: ${({ disabled }) =>
      disabled
        ? "linear-gradient(to bottom, rgb(145, 145, 145) 30%, rgb(130, 130, 130) 100%);"
        : "linear-gradient(to bottom, rgb(27, 112, 187) 30%, rgb(21, 89, 150) 100%);"}
  }

  &:active {
    background-color: ${Colors.GRAY3};
  }

  path.bp3-spinner-head {
    stroke: white;
  }
`;
