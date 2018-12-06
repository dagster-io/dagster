import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, Button, InputGroup } from "@blueprintjs/core";
import { PipelineRunFilteredLogMessageFragment } from "./types/PipelineRunFilteredLogMessageFragment";

interface IPipelineRunFilteredLogsProps {
  filter: string;
  onSetFilter: (filter: string) => void;
  nodes: PipelineRunFilteredLogMessageFragment[];
}

type LogLevel = "info" | "normal" | "error";

function logLevelForMessage(message: string): LogLevel {
  if (message.includes("About to execute")) {
    return "info";
  }
  if (message.includes("oops")) {
    return "info";
  }
  if (message.includes("failed") || message.includes("Error ")) {
    return "error";
  }
  return "normal";
}

export default class PipelineRunFilteredLogs extends React.Component<
  IPipelineRunFilteredLogsProps
> {
  static fragments = {
    PipelineRunFilteredLogMessageFragment: gql`
      fragment PipelineRunFilteredLogMessageFragment on PipelineRunEvent {
        __typename
        ... on MessageEvent {
          message
        }
      }
    `
  };

  render() {
    const { filter, nodes } = this.props;

    const filteredNodes = filter
      ? nodes.filter(node => node.message.includes(filter))
      : nodes;

    return (
      <>
        <LogsToolbar>
          <InputGroup
            leftIcon="filter"
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              this.props.onSetFilter(e.target.value)
            }
            placeholder="Filter logs..."
            // rightElement={maybeSpinner}
            small={true}
            value={filter}
          />
          <LogsToolbarDivider />
          <Button className="bp3-minimal" icon="home" text="Home" />
          <Button className="bp3-minimal" icon="document" text="Files" />
        </LogsToolbar>
        <div style={{ overflowY: "scroll", flex: 1 }}>
          {filteredNodes.map((log, i) => (
            <LogMessage level={logLevelForMessage(log.message)} key={i}>
              {log.message}
            </LogMessage>
          ))}
        </div>
      </>
    );
  }
}

const LogsToolbar = styled.div`
  display: flex;
  flex-direction: row;
  background: ${Colors.WHITE};
  height: 40px;
  align-items: center;
  padding: 10px 5px;
`;

const LogsToolbarDivider = styled.div`
  display: inline-block;
  width: 1px;
  height: 30px;
  background: ${Colors.LIGHT_GRAY3};
`;

const LogMessage = styled.div<{ level: LogLevel }>`
  color: ${props =>
    ({
      info: Colors.GRAY3,
      normal: Colors.DARK_GRAY2,
      error: Colors.RED3
    }[props.level])};
  padding: 5px;
  font-size: 0.9em;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY3};
`;
