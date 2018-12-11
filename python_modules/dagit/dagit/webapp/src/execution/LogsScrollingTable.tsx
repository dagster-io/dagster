import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { LogsScrollingTableMessageFragment } from "./types/LogsScrollingTableMessageFragment";
import { LogLevel } from "./LogsFilterProvider";

interface ILogsScrollingTableProps {
  nodes: LogsScrollingTableMessageFragment[];
}

function textForLog(log: LogsScrollingTableMessageFragment) {
  if (log.__typename === "ExecutionStepFailureEvent") {
    return `${log.message}\n${log.error.message}\n${log.error.stack}`;
  }
  return log.message;
}

export default class LogsScrollingTable extends React.Component<
  ILogsScrollingTableProps,
  {}
> {
  static fragments = {
    LogsScrollingTableMessageFragment: gql`
      fragment LogsScrollingTableMessageFragment on PipelineRunEvent {
        __typename
        ... on MessageEvent {
          message
          timestamp
          level
        }
        ... on ExecutionStepFailureEvent {
          message
          level
          step {
            name
          }
          error {
            stack
            message
          }
        }
      }
    `
  };

  render() {
    return (
      <div style={{ overflowY: "scroll", flex: 1 }}>
        {this.props.nodes.map((log, i) => (
          <LogMessage level={log.level} key={i}>
            {textForLog(log)}
          </LogMessage>
        ))}
      </div>
    );
  }
}

const LogMessage = styled.div<{ level: LogLevel }>`
  color: ${props =>
    ({
      [LogLevel.DEBUG]: Colors.GRAY3,
      [LogLevel.INFO]: Colors.DARK_GRAY2,
      [LogLevel.WARNING]: Colors.DARK_GRAY2,
      [LogLevel.ERROR]: Colors.RED3,
      [LogLevel.CRITICAL]: Colors.RED3
    }[props.level])};
  padding: 4px;
  padding-left: 15px;
  font-size: 0.85em;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY3};
  word-break: break-all;
  white-space: pre-wrap;
`;
