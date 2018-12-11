import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, NonIdealState } from "@blueprintjs/core";
import { LogsScrollingTableMessageFragment } from "./types/LogsScrollingTableMessageFragment";
import { LogLevel } from "./LogsFilterProvider";
import {
  CellMeasurer,
  CellMeasurerCache,
  AutoSizer,
  Grid,
  GridCellProps
} from "react-virtualized";
import { IconNames } from "@blueprintjs/icons";

const cache = new CellMeasurerCache({
  defaultHeight: 30,
  fixedWidth: true
});

interface ILogsScrollingTableProps {
  nodes: LogsScrollingTableMessageFragment[];
}

interface ILogsScrollingTableSizedProps extends ILogsScrollingTableProps {
  width: number;
  height: number;
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
      <div style={{ flex: 1 }}>
        <AutoSizer>
          {({ width, height }) => (
            <LogsScrollingTableSized
              {...this.props}
              width={width}
              height={height}
            />
          )}
        </AutoSizer>
      </div>
    );
  }
}

class LogsScrollingTableSized extends React.Component<
  ILogsScrollingTableSizedProps
> {
  componentDidUpdate() {
    cache.clearAll();
  }

  cellRenderer = ({
    parent,
    rowIndex,
    columnIndex,
    key,
    style
  }: GridCellProps) => {
    const node = this.props.nodes[rowIndex];
    const width = this.columnWidth({ index: columnIndex });

    let content = null;
    switch (columnIndex) {
      case 0:
        content = node.level;
        break;
      case 1:
        content = textForLog(node);
        break;
      case 2:
        content = new Date(Number(node.timestamp)).toLocaleString();
        break;
    }

    return (
      <CellMeasurer
        cache={cache}
        rowIndex={rowIndex}
        columnIndex={columnIndex}
        parent={parent}
        key={key}
      >
        <Cell style={{ ...style, width }} level={node.level}>
          {content}
        </Cell>
      </CellMeasurer>
    );
  };

  noContentRenderer = () => {
    return (
      <NonIdealState icon={IconNames.CONSOLE} title="No logs to display" />
    );
  };

  columnWidth = ({ index }: { index: number }) => {
    switch (index) {
      case 0:
        return 80;
      case 1:
        return this.props.width - 170 - 80;
      case 2:
        return 170;
      default:
        return 80;
    }
  };

  render() {
    return (
      <LogsGrid
        key={`${this.props.width}-${this.props.height}`}
        cellRenderer={this.cellRenderer}
        columnWidth={this.columnWidth}
        columnCount={3}
        width={this.props.width}
        height={this.props.height}
        deferredMeasurementCache={cache}
        rowHeight={cache.rowHeight}
        noContentRenderer={this.noContentRenderer}
        overscanColumnCount={0}
        overscanRowCount={10}
        rowCount={this.props.nodes.length}
      />
    );
  }
}

const LogsGrid = styled(Grid)`
  width: 100%;
  border: 1px solid #e0e0e0;
`;

const Cell = styled.div<{ level: LogLevel }>`
  font-size: 0.85em;
  width: 100%;
  height: 100%;
  padding: 4px;
  padding-left: 15px;
  word-break: break-all;
  white-space: pre-wrap;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY3};
  background: ${props =>
    LogLevel.ERROR === props.level || LogLevel.CRITICAL === props.level
      ? `rgba(206, 17, 38, 0.05)`
      : `transparent`};
  color: ${props =>
    ({
      [LogLevel.DEBUG]: Colors.GRAY3,
      [LogLevel.INFO]: Colors.DARK_GRAY2,
      [LogLevel.WARNING]: Colors.DARK_GRAY2,
      [LogLevel.ERROR]: Colors.RED3,
      [LogLevel.CRITICAL]: Colors.RED3
    }[props.level])};
`;
