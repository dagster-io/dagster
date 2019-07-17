import * as React from "react";
import * as ReactDOM from "react-dom";
import gql from "graphql-tag";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import {
  CellMeasurer,
  CellMeasurerCache,
  AutoSizer,
  ListRowProps,
  List
} from "react-virtualized";

import * as LogsRow from "./LogsRow";
import { CellTruncationProvider } from "./CellTruncationProvider";
import { LogsScrollingTableMessageFragment } from "./types/LogsScrollingTableMessageFragment";
import {
  Headers,
  ColumnWidthsContext,
  DefaultColumnWidths
} from "./LogsRowComponents";

interface ILogsScrollingTableProps {
  nodes?: LogsScrollingTableMessageFragment[];
}

interface ILogsScrollingTableSizedProps extends ILogsScrollingTableProps {
  width: number;
  height: number;
}

interface ILogsScrollingTableSizedState {
  columnWidths: typeof DefaultColumnWidths;
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
  list = React.createRef<List>();

  state = {
    columnWidths: DefaultColumnWidths
  };
  get listEl() {
    const el = this.list.current && ReactDOM.findDOMNode(this.list.current);
    if (!(el instanceof HTMLElement)) {
      return null;
    }
    return el;
  }

  cache = new CellMeasurerCache({
    defaultHeight: 30,
    fixedWidth: true,
    keyMapper: (rowIndex: number) =>
      `${this.props.nodes && this.props.nodes[rowIndex].message}`
  });

  isAtBottomOrZero: boolean = true;
  scrollToBottomObserver: MutationObserver;

  componentDidMount() {
    this.attachScrollToBottomObserver();
  }

  componentDidUpdate(prevProps: ILogsScrollingTableSizedProps) {
    if (!this.list.current) return;

    if (this.props.width !== prevProps.width) {
      this.cache.clearAll();
    }
    if (this.props.nodes !== prevProps.nodes) {
      this.list.current.recomputeGridSize();
    }
  }

  componentWillUnmount() {
    if (this.scrollToBottomObserver) {
      this.scrollToBottomObserver.disconnect();
    }
  }

  attachScrollToBottomObserver() {
    const el = this.listEl;
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
    if (!this.list.current) return;

    const { scrollTop, scrollHeight, clientHeight } = e.target as Element;
    const atTopAndStarting = scrollTop === 0 && scrollHeight <= clientHeight;
    const atBottom = Math.abs(scrollTop - (scrollHeight - clientHeight)) < 5;
    this.isAtBottomOrZero = atTopAndStarting || atBottom;

    (this.list.current as any)._onScroll(e.target as Element);
  };

  rowRenderer = ({ parent, index, key, style }: ListRowProps) => {
    if (!this.props.nodes) return;
    const node = this.props.nodes[index];
    if (!node) return <span />;

    return (
      <CellMeasurer
        cache={this.cache}
        rowIndex={index}
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
        <ColumnWidthsContext.Provider
          value={{
            ...this.state.columnWidths,
            onChange: columnWidths => this.setState({ columnWidths })
          }}
        >
          <Headers />
          <List
            deferredMeasurementCache={this.cache}
            overscanRowCount={10}
            rowCount={this.props.nodes ? this.props.nodes.length : 0}
            noContentRenderer={this.noContentRenderer}
            rowHeight={this.cache.rowHeight}
            rowRenderer={this.rowRenderer}
            width={this.props.width}
            height={this.props.height}
          />
        </ColumnWidthsContext.Provider>
      </div>
    );
  }
}
