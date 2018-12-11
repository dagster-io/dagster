import * as React from "react";
import * as ReactDOM from "react-dom";
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

interface ILogsScrollingTableProps {
  nodes: LogsScrollingTableMessageFragment[];
}

interface ILogsScrollingTableSizedProps extends ILogsScrollingTableProps {
  width: number;
  height: number;
}

interface ILogsScrollingTableSizedState {
  scrollTop: number;
}

function settle(fn: () => boolean): void {
  let count = 0;
  const step = () => {
    count += 1;
    if (fn() && count < 5) {
      window.requestAnimationFrame(step);
    }
  };
  step();
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
  ILogsScrollingTableSizedProps,
  ILogsScrollingTableSizedState
> {
  grid = React.createRef<Grid>();

  cache = new CellMeasurerCache({
    defaultHeight: 30,
    fixedWidth: true,
    keyMapper: (rowIndex: number, columnIndex: number) =>
      `${this.props.nodes[rowIndex].message}:${columnIndex}`
  });

  isAtBottomOrZero: boolean = true;

  componentDidUpdate(prevProps: ILogsScrollingTableSizedProps) {
    if (this.props.width !== prevProps.width) {
      this.cache.clearAll();
    }

    if (this.isAtBottomOrZero) {
      this.scrollToBottom();
    }
  }

  scrollToBottom = () => {
    if (!this.grid.current) return;
    const el = ReactDOM.findDOMNode(this.grid.current);
    if (!(el instanceof Element)) return;

    /*
    Note BG: Not happy about this. If you change the width of the grid, the
    component renders and /then/ computes the heights of cells. We need to
    push the scroll offset to the bottom repeatedly as the grid's scrollHeight
    is finalized.
    */
    settle(() => {
      const target = el.scrollHeight - el.clientHeight;
      if (!this.isAtBottomOrZero) return false;
      if (Math.abs(el.scrollTop - target) < 2) return false;
      el.scrollTop = target;
      return true;
    });
  };

  onScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (!this.grid.current) return;

    const target = e.target as Element;
    this.isAtBottomOrZero =
      target.scrollTop === 0 ||
      Math.abs(target.scrollTop - (target.scrollHeight - target.clientHeight)) <
        5;

    this.grid.current.handleScrollEvent(target);
  };

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
        style.textAlign = "right";
        content = new Date(Number(node.timestamp))
          .toISOString()
          .replace("Z", "")
          .split("T")
          .pop();
        break;
    }

    return (
      <CellMeasurer
        cache={this.cache}
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
        return this.props.width - 110 - 80;
      case 2:
        return 110;
      default:
        return 0;
    }
  };

  render() {
    return (
      <div onScroll={this.onScroll}>
        <Grid
          ref={this.grid}
          cellRenderer={this.cellRenderer}
          columnWidth={this.columnWidth}
          columnCount={3}
          width={this.props.width}
          height={this.props.height}
          deferredMeasurementCache={this.cache}
          rowHeight={this.cache.rowHeight}
          rowCount={this.props.nodes.length}
          noContentRenderer={this.noContentRenderer}
          overscanColumnCount={0}
          overscanRowCount={20}
        />
      </div>
    );
  }
}

const Cell = styled.div<{ level: LogLevel }>`
  font-size: 0.85em;
  width: 100%;
  height: 100%;
  padding: 4px;
  padding-left: 15px;
  word-break: break-all;
  white-space: pre-wrap;
  font-family: monospace;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY3};
  background: ${props =>
    ({
      [LogLevel.DEBUG]: `transparent`,
      [LogLevel.INFO]: `transparent`,
      [LogLevel.WARNING]: `rgba(166, 121, 8, 0.05)`,
      [LogLevel.ERROR]: `rgba(206, 17, 38, 0.05)`,
      [LogLevel.CRITICAL]: `rgba(206, 17, 38, 0.05)`
    }[props.level])};
  color: ${props =>
    ({
      [LogLevel.DEBUG]: Colors.GRAY3,
      [LogLevel.INFO]: Colors.DARK_GRAY2,
      [LogLevel.WARNING]: Colors.GOLD2,
      [LogLevel.ERROR]: Colors.RED3,
      [LogLevel.CRITICAL]: Colors.RED3
    }[props.level])};
`;
