import * as React from "react";
import * as ReactDOM from "react-dom";
import gql from "graphql-tag";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import {
  CellMeasurer,
  CellMeasurerCache,
  AutoSizer,
  Grid,
  GridCellProps
} from "react-virtualized";

import * as LogsRow from "./LogsRow";
import { CellTruncationProvider } from "./Cells";
import { LogsScrollingTableMessageFragment } from "./types/LogsScrollingTableMessageFragment";

interface ILogsScrollingTableProps {
  nodes?: LogsScrollingTableMessageFragment[];
}

interface ILogsScrollingTableSizedProps extends ILogsScrollingTableProps {
  width: number;
  height: number;
}

interface ILogsScrollingTableSizedState {
  scrollTop: number;
}

export default class LogsScrollingTable extends React.Component<
  ILogsScrollingTableProps
> {
  static fragments = {
    LogsScrollingTableMessageFragment: gql`
      fragment LogsScrollingTableMessageFragment on PipelineRunEvent {
        __typename
        ...LogsRowStructuredFragment
        ...LogsRowUnstructuredFragment
      }

      ${LogsRow.Structured.fragments.LogsRowStructuredFragment}
      ${LogsRow.Unstructured.fragments.LogsRowUnstructuredFragment}
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

  get gridEl() {
    const el = this.grid.current && ReactDOM.findDOMNode(this.grid.current);
    if (!(el instanceof HTMLElement)) {
      return null;
    }
    return el;
  }

  cache = new CellMeasurerCache({
    defaultHeight: 30,
    fixedWidth: true,
    keyMapper: (rowIndex: number, columnIndex: number) =>
      `${this.props.nodes && this.props.nodes[rowIndex].message}:${columnIndex}`
  });

  isAtBottomOrZero: boolean = true;
  scrollToBottomObserver: MutationObserver;

  componentDidMount() {
    this.attachScrollToBottomObserver();
  }

  componentDidUpdate(prevProps: ILogsScrollingTableSizedProps) {
    if (!this.grid.current) return;

    if (this.props.width !== prevProps.width) {
      this.cache.clearAll();
    }
    if (this.props.nodes !== prevProps.nodes) {
      this.grid.current.recomputeGridSize();
    }
  }

  componentWillUnmount() {
    if (this.scrollToBottomObserver) {
      this.scrollToBottomObserver.disconnect();
    }
  }

  attachScrollToBottomObserver() {
    const el = this.gridEl;
    if (!el) return;

    let lastHeight: string | null = null;

    this.scrollToBottomObserver = new MutationObserver(() => {
      const rowgroupEl = el.querySelector("[role=rowgroup]") as HTMLElement;
      if (!rowgroupEl) {
        lastHeight = null;
        return;
      }
      if (rowgroupEl.style.height === lastHeight) return;
      if (!this.isAtBottomOrZero) return;

      lastHeight = rowgroupEl.style.height;
      el.scrollTop = el.scrollHeight - el.clientHeight;
    });

    this.scrollToBottomObserver.observe(el, {
      attributes: true,
      subtree: true
    });
  }

  onScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (!this.grid.current) return;

    const { scrollTop, scrollHeight, clientHeight } = e.target as Element;
    const atTopAndStarting = scrollTop === 0 && scrollHeight <= clientHeight;
    const atBottom = Math.abs(scrollTop - (scrollHeight - clientHeight)) < 5;
    this.isAtBottomOrZero = atTopAndStarting || atBottom;

    this.grid.current.handleScrollEvent(e.target as Element);
  };

  cellRenderer = ({
    parent,
    rowIndex,
    columnIndex,
    key,
    style
  }: GridCellProps) => {
    if (!this.props.nodes) return;
    const node = this.props.nodes[rowIndex];
    if (!node) return <span />;

    return (
      <CellMeasurer
        cache={this.cache}
        rowIndex={rowIndex}
        columnIndex={columnIndex}
        parent={parent}
        key={key}
      >
        <CellTruncationProvider style={{ ...style, width: this.props.width }}>
          {node.__typename === "LogMessageEvent" ? (
            <LogsRow.Unstructured node={node} />
          ) : (
            <LogsRow.Structured node={node} />
          )}
        </CellTruncationProvider>
      </CellMeasurer>
    );
  };

  noContentRenderer = () => {
    if (this.props.nodes) {
      return (
        <NonIdealState icon={IconNames.CONSOLE} title="No logs to display" />
      );
    }
    return <span />;
  };

  render() {
    return (
      <div onScroll={this.onScroll}>
        <Grid
          ref={this.grid}
          cellRenderer={this.cellRenderer}
          columnWidth={() => this.props.width}
          columnCount={1}
          width={this.props.width}
          height={this.props.height}
          autoContainerWidth={true}
          deferredMeasurementCache={this.cache}
          rowHeight={this.cache.rowHeight}
          rowCount={this.props.nodes ? this.props.nodes.length : 0}
          noContentRenderer={this.noContentRenderer}
          overscanColumnCount={0}
          overscanRowCount={20}
        />
      </div>
    );
  }
}
