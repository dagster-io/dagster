import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { LogsScrollingTableMessageFragment } from "./types/LogsScrollingTableMessageFragment";
import { LogLevel } from "./LogsFilterProvider";
import { AutoSizer, Grid, GridCellProps } from "react-virtualized";

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

  _cellRenderer = ({ columnIndex, key, rowIndex, style }: GridCellProps) => {
    const node = this.props.nodes[rowIndex];
    switch (columnIndex) {
      case 0:
        return (
          <Cell key={key} style={style}>
            {node.level}
          </Cell>
        );
      case 1:
        return (
          <Cell key={key} style={style}>
            {textForLog(node)}
          </Cell>
        );
      case 2:
        return (
          <Cell key={key} style={style}>
            {new Date(Number(node.timestamp)).toLocaleString()}
          </Cell>
        );
    }
    return false;
  };

  _noContentRenderer = () => {
    return <div>No cells</div>;
  };

  render() {
    return (
      <AutoSizer>
        {({ width, height }) => (
          <BodyGrid
            cellRenderer={this._cellRenderer}
            columnWidth={({ index }: { index: number }) => {
              switch (index) {
                case 0:
                  return 50;
                case 1:
                  return width - 50 - 150;
                case 2:
                  return 150;
                default:
                  return 80;
              }
            }}
            columnCount={3}
            width={width}
            height={height}
            noContentRenderer={this._noContentRenderer}
            overscanColumnCount={0}
            overscanRowCount={10}
            rowHeight={40}
            rowCount={this.props.nodes.length}
          />
        )}
      </AutoSizer>
    );
  }
}

const BodyGrid = styled(Grid)`
  width: 100%;
  border: 1px solid #e0e0e0;
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

const Cell = styled.div`
  font-size: 0.85em;
  width: 100%;
  height: 100%;
  display: flex;
  padding: 4px;
  padding-left: 15px;
  word-break: break-all;
  white-space: pre-wrap;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY3};
`;
