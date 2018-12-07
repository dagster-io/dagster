import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, Button, ButtonGroup, InputGroup } from "@blueprintjs/core";
import { PipelineRunFilteredLogMessageFragment } from "./types/PipelineRunFilteredLogMessageFragment";
import { IconNames } from "@blueprintjs/icons";

interface IPipelineRunFilteredLogsProps {
  filter: string;
  onSetFilter: (filter: string) => void;
  nodes: PipelineRunFilteredLogMessageFragment[];
}

interface IPipelineRunFilteredLogsState {
  clearedAtTimestamp: number;
  enabledLevels: { [key: string]: boolean };
}

type LogLevel = "info" | "normal" | "error";

const LogLevels: LogLevel[] = ["info", "normal", "error"];

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

function textForLog(log: PipelineRunFilteredLogMessageFragment) {
  if (log.__typename === "ExecutionStepFailureEvent") {
    return `${log.message}\n${log.error.message}\n${log.error.stack}`;
  }
  return log.message;
}

export default class PipelineRunFilteredLogs extends React.Component<
  IPipelineRunFilteredLogsProps,
  IPipelineRunFilteredLogsState
> {
  static fragments = {
    PipelineRunFilteredLogMessageFragment: gql`
      fragment PipelineRunFilteredLogMessageFragment on PipelineRunEvent {
        __typename
        ... on MessageEvent {
          message
          timestamp
        }
        ... on ExecutionStepFailureEvent {
          message
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

  state = {
    clearedAtTimestamp: 0,
    enabledLevels: {
      info: true,
      normal: true,
      error: true
    }
  };

  render() {
    const { filter, nodes } = this.props;
    const { clearedAtTimestamp, enabledLevels } = this.state;

    let displayed = nodes.filter(
      node => enabledLevels[logLevelForMessage(node.message)]
    );

    if (clearedAtTimestamp > 0) {
      const indexAfter = displayed.findIndex(
        node => Number(node.timestamp) > clearedAtTimestamp
      );
      displayed = indexAfter === -1 ? [] : displayed.slice(indexAfter);
    }
    if (filter) {
      displayed = displayed.filter(node => node.message.includes(filter));
    }

    return (
      <>
        <LogsToolbar>
          <FilterInputGroup
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
          <ButtonGroup>
            {LogLevels.map(level => (
              <Button
                text={level}
                small={true}
                active={enabledLevels[level]}
                onClick={() =>
                  this.setState({
                    enabledLevels: {
                      ...enabledLevels,
                      [level]: !enabledLevels[level]
                    }
                  })
                }
              />
            ))}
          </ButtonGroup>
          <div style={{ flex: 1 }} />
          <Button
            text={"Clear"}
            small={true}
            icon={IconNames.CLEAN}
            onClick={() => this.setState({ clearedAtTimestamp: Date.now() })}
          />
        </LogsToolbar>
        <div style={{ overflowY: "scroll", flex: 1 }}>
          {displayed.map((log, i) => (
            <LogMessage level={logLevelForMessage(log.message)} key={i}>
              {textForLog(log)}
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
  padding: 5px 15px;
  border-bottom: 1px solid ${Colors.GRAY4};
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.07);
`;

const LogsToolbarDivider = styled.div`
  display: inline-block;
  width: 1px;
  height: 30px;
  margin: 0 15px;
  border-right: 1px solid ${Colors.LIGHT_GRAY3};
`;

const FilterInputGroup = styled(InputGroup)`
  flex: 2;
  max-width: 275px;
  min-width: 100px;
`;

const LogMessage = styled.div<{ level: LogLevel }>`
  color: ${props =>
    ({
      info: Colors.GRAY3,
      normal: Colors.DARK_GRAY2,
      error: Colors.RED3
    }[props.level])};
  padding: 4px;
  padding-left: 15px;
  font-size: 0.85em;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY3};
  word-break: break-all;
  white-space: pre-wrap;
`;
