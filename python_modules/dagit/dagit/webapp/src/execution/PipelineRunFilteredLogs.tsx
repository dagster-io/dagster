import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, Button, ButtonGroup, InputGroup } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { PipelineRunFilteredLogMessageFragment } from "./types/PipelineRunFilteredLogMessageFragment";

interface IPipelineRunFilteredLogsProps {
  filter: string;
  onSetFilter: (filter: string) => void;
  nodes: PipelineRunFilteredLogMessageFragment[];
}

interface IPipelineRunFilteredLogsState {
  clearedAtTimestamp: number;
  enabledLevels: { [key: string]: boolean };
}

enum LogLevel {
  DEBUG = "DEBUG",
  INFO = "INFO",
  WARNING = "WARNING",
  ERROR = "ERROR",
  CRITICAL = "CRITICAL"
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

  state = {
    clearedAtTimestamp: 0,
    enabledLevels: Object.keys(LogLevel).reduce(
      (dict, key) => ({ ...dict, [key]: true }),
      {}
    )
  };

  render() {
    const { filter, nodes } = this.props;
    const { clearedAtTimestamp, enabledLevels } = this.state;

    let displayed = nodes.filter(node => enabledLevels[node.level]);

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
            {Object.keys(LogLevel).map(level => (
              <Button
                text={level.toLowerCase()}
                small={true}
                style={{ textTransform: "capitalize" }}
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
            icon={IconNames.ERASER}
            onClick={() => this.setState({ clearedAtTimestamp: Date.now() })}
          />
        </LogsToolbar>
        <div style={{ overflowY: "scroll", flex: 1 }}>
          {displayed.map((log, i) => (
            <LogMessage level={log.level} key={i}>
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
