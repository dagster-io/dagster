import * as React from "react";
import styled from "styled-components";
import { Icon, Intent, Spinner, Colors } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { WebsocketStatusContext } from "../WebsocketStatus";

interface IExecutionStartButtonProps {
  isExecuting: boolean;
  onClick: () => void;
}

export default function ExecutionStartButton(
  props: IExecutionStartButtonProps
) {
  return (
    <WebsocketStatusContext.Consumer>
      {websocketStatus => {
        if (props.isExecuting) {
          return (
            <IconWrapper
              role="button"
              title={"Pipeline execution is in progress..."}
            >
              <Spinner intent={Intent.NONE} size={39} />
            </IconWrapper>
          );
        }

        if (websocketStatus !== WebSocket.OPEN) {
          return (
            <IconWrapper
              role="button"
              disabled={true}
              title={"Dagit is disconnected"}
            >
              <Icon icon={IconNames.OFFLINE} iconSize={40} />
            </IconWrapper>
          );
        }

        return (
          <IconWrapper
            role="button"
            title={"Start pipeline execution"}
            onClick={props.onClick}
          >
            <Icon icon={IconNames.PLAY} iconSize={40} />
          </IconWrapper>
        );
      }}
    </WebsocketStatusContext.Consumer>
  );
}

const IconWrapper = styled.div<{ disabled?: boolean }>`
  flex: 0 1 0;
  width: 60px;
  height: 60px;
  border-radius: 30px;
  background: ${({ disabled }) =>
    disabled
      ? "linear-gradient(to bottom, rgb(145, 145, 145) 30%, rgb(130, 130, 130) 100%);"
      : "linear-gradient(to bottom, rgb(36, 145, 235) 30%, rgb(27, 112, 187) 100%);"}
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
  border-top: 1px solid rgba(255,255,255,0.25);
  border-bottom: 1px solid rgba(0,0,0,0.25);
  transition: background 200ms linear;
  position: absolute;
  top: 20px;
  right: 20px;
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
