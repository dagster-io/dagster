import {gql} from '@apollo/client';
import {Colors, NonIdealState, Spinner} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import * as ReactDOM from 'react-dom';
import {CellMeasurer, CellMeasurerCache, List, ListRowProps} from 'react-virtualized';
import styled from 'styled-components/macro';

import {LogFilter, LogsProviderLogs} from 'src/runs/LogsProvider';
import {
  LOGS_ROW_STRUCTURED_FRAGMENT,
  LOGS_ROW_UNSTRUCTURED_FRAGMENT,
  Structured,
  Unstructured,
} from 'src/runs/LogsRow';
import {ColumnWidthsProvider, Headers} from 'src/runs/LogsScrollingTableHeader';
import {IRunMetadataDict} from 'src/runs/RunMetadataProvider';
import {RunPipelineRunEventFragment} from 'src/runs/types/RunPipelineRunEventFragment';

interface ILogsScrollingTableProps {
  logs: LogsProviderLogs;
  filter: LogFilter;
  filterStepKeys: string[];

  // We use this string to know whether the changes to `nodes` require us to
  // re-layout the entire table. Appending new rows can be done very fast, but
  // removing some rows requires the whole list be "reflowed" again. Checking
  // `nodes` for equality doesn't let us optimize for the append- case.
  filterKey: string;
  metadata: IRunMetadataDict;
}

interface ILogsScrollingTableSizedProps {
  width: number;
  height: number;

  filteredNodes: (RunPipelineRunEventFragment & {clientsideKey: string})[];
  textMatchNodes: (RunPipelineRunEventFragment & {clientsideKey: string})[];

  filterKey: string;
  loading: boolean;
  focusedTime: number;
  metadata: IRunMetadataDict;
}

function filterLogs(logs: LogsProviderLogs, filter: LogFilter, filterStepKeys: string[]) {
  const filteredNodes = logs.allNodes.filter((node) => {
    const l = node.__typename === 'LogMessageEvent' ? node.level : 'EVENT';
    if (!filter.levels[l]) {
      return false;
    }
    if (filter.sinceTime && Number(node.timestamp) < filter.sinceTime) {
      return false;
    }
    return true;
  });

  const hasTextFilter = !!(filter.logQuery.length && filter.logQuery[0].value !== '');

  const textMatchNodes = hasTextFilter
    ? filteredNodes.filter((node) => {
        return (
          filter.logQuery.length > 0 &&
          filter.logQuery.every((f) => {
            if (f.token === 'query') {
              return node.stepKey && filterStepKeys.includes(node.stepKey);
            }
            if (f.token === 'step') {
              return node.stepKey && node.stepKey === f.value;
            }
            if (f.token === 'type') {
              return node.__typename.toLowerCase().includes(f.value);
            }
            return node.message.toLowerCase().includes(f.value.toLowerCase());
          })
        );
      })
    : [];

  return {
    filteredNodes: hasTextFilter && filter.hideNonMatches ? textMatchNodes : filteredNodes,
    textMatchNodes: textMatchNodes,
  };
}

export class LogsScrollingTable extends React.Component<ILogsScrollingTableProps> {
  table = React.createRef<LogsScrollingTableSized>();

  render() {
    const {filterKey, filterStepKeys, metadata, filter, logs} = this.props;

    return (
      <ColumnWidthsProvider
        onWidthsChanged={() => this.table.current && this.table.current.didResize()}
      >
        <Headers />
        <div style={{flex: 1, minHeight: 0}}>
          <AutoSizer>
            {({width, height}) => (
              <LogsScrollingTableSized
                width={width}
                height={height}
                ref={this.table}
                filterKey={filterKey}
                loading={logs.loading}
                metadata={metadata}
                focusedTime={filter.focusedTime}
                {...filterLogs(logs, filter, filterStepKeys)}
              />
            )}
          </AutoSizer>
        </div>
      </ColumnWidthsProvider>
    );
  }
}

export const LOGS_SCROLLING_TABLE_MESSAGE_FRAGMENT = gql`
  fragment LogsScrollingTableMessageFragment on PipelineRunEvent {
    __typename
    ...LogsRowStructuredFragment
    ...LogsRowUnstructuredFragment
  }

  ${LOGS_ROW_STRUCTURED_FRAGMENT}
  ${LOGS_ROW_UNSTRUCTURED_FRAGMENT}
`;

class LogsScrollingTableSized extends React.Component<ILogsScrollingTableSizedProps> {
  list = React.createRef<List>();

  get listEl() {
    // eslint-disable-next-line react/no-find-dom-node
    const el = this.list.current && ReactDOM.findDOMNode(this.list.current);
    if (!(el instanceof HTMLElement)) {
      return null;
    }
    return el;
  }

  cache = new CellMeasurerCache({
    defaultHeight: 30,
    fixedWidth: true,
    keyMapper: (rowIndex) =>
      this.props.filteredNodes ? this.props.filteredNodes[rowIndex].clientsideKey : '',
  });

  isAtBottomOrZero = true;
  scrollToBottomObserver: MutationObserver;

  componentDidMount() {
    this.attachScrollToBottomObserver();
  }

  componentDidUpdate(prevProps: ILogsScrollingTableSizedProps) {
    if (!this.list.current) {
      return;
    }

    if (this.props.width !== prevProps.width) {
      this.didResize();
    }
    if (this.props.filterKey !== prevProps.filterKey) {
      this.list.current.recomputeGridSize();
    }

    if (
      this.props.focusedTime &&
      this.props.filteredNodes?.length !== prevProps.filteredNodes?.length
    ) {
      window.requestAnimationFrame(() => {
        this.scrollToTime(this.props.focusedTime);
      });
    }
  }

  componentWillUnmount() {
    if (this.scrollToBottomObserver) {
      this.scrollToBottomObserver.disconnect();
    }
  }

  didResize() {
    this.cache.clearAll();
    this.forceUpdate();
  }

  attachScrollToBottomObserver() {
    const el = this.listEl;
    if (!el) {
      console.warn(`No container, LogsScrollingTable must render listEl`);
      return;
    }

    let lastHeight: string | null = null;

    this.scrollToBottomObserver = new MutationObserver(() => {
      const rowgroupEl = el.querySelector('[role=rowgroup]') as HTMLElement;
      if (!rowgroupEl) {
        lastHeight = null;
        return;
      }
      if (rowgroupEl.style.height === lastHeight) {
        return;
      }
      if (!this.isAtBottomOrZero) {
        return;
      }

      lastHeight = rowgroupEl.style.height;
      el.scrollTop = el.scrollHeight - el.clientHeight;
    });

    this.scrollToBottomObserver.observe(el, {
      attributes: true,
      subtree: true,
    });
  }

  onScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (!this.list.current) {
      return;
    }

    const {scrollTop, scrollHeight, clientHeight} = e.target as Element;
    const atTopAndStarting = scrollTop === 0 && scrollHeight <= clientHeight;
    const atBottom = Math.abs(scrollTop - (scrollHeight - clientHeight)) < 5;
    this.isAtBottomOrZero = atTopAndStarting || atBottom;

    (this.list.current as any)._onScroll(e.target as Element);
  };

  scrollToTime = (ms: number) => {
    if (!this.props.filteredNodes || !this.list.current) {
      return;
    }

    // Stop the table from attempting to return to the bottom-of-feed
    // if more logs arrive.
    this.isAtBottomOrZero = false;

    // Find the row immediately at or after the provided timestamp
    const target: {index: number; alignment: 'center'} = {
      index: this.props.filteredNodes.findIndex((n) => Number(n.timestamp) >= ms),
      alignment: 'center',
    };
    if (target.index === -1) {
      target.index = this.props.filteredNodes.length - 1;
    }

    // Move to the offset. For some reason, this takes multiple iterations but not multiple renders.
    // It seems react-virtualized may be using default row height for rows more than X rows away and
    // the number gets more accurate as we scroll, which is very annoying.
    let offset = 0;
    let iterations = 0;
    while (offset !== this.list.current.getOffsetForRow(target)) {
      offset = this.list.current.getOffsetForRow(target);
      this.list.current.scrollToPosition(offset);
      iterations += 1;
      if (iterations > 20) {
        break;
      }
    }
  };

  rowRenderer = ({parent, index, style}: ListRowProps) => {
    if (!this.props.filteredNodes) {
      return;
    }
    const node = this.props.filteredNodes[index];
    const focusedTimeMatch = Number(node.timestamp) === this.props.focusedTime;
    const textMatch = !!this.props.textMatchNodes?.includes(node);

    const metadata = this.props.metadata;
    if (!node) {
      return <span />;
    }
    const isLastRow = index === this.props.filteredNodes.length - 1;
    const lastRowStyles = isLastRow
      ? {
          borderBottom: `1px solid ${Colors.LIGHT_GRAY3}`,
        }
      : {};

    return (
      <CellMeasurer cache={this.cache} index={index} parent={parent} key={node.clientsideKey}>
        {node.__typename === 'LogMessageEvent' ? (
          <Unstructured
            node={node}
            style={{...style, width: this.props.width, ...lastRowStyles}}
            highlighted={textMatch || focusedTimeMatch}
          />
        ) : (
          <Structured
            node={node}
            metadata={metadata}
            style={{...style, width: this.props.width, ...lastRowStyles}}
            highlighted={textMatch || focusedTimeMatch}
          />
        )}
      </CellMeasurer>
    );
  };

  noContentRenderer = () => {
    if (this.props.filteredNodes) {
      return <NonIdealState icon={IconNames.CONSOLE} title="No logs to display" />;
    }
    return <span />;
  };

  render() {
    const {filteredNodes, height, loading, width} = this.props;
    return (
      <div onScroll={this.onScroll}>
        {loading && (
          <ListEmptyState>
            <NonIdealState icon={<Spinner size={24} />} title="Fetching logs..." />
          </ListEmptyState>
        )}
        <List
          ref={this.list}
          deferredMeasurementCache={this.cache}
          rowCount={filteredNodes?.length || 0}
          noContentRenderer={this.noContentRenderer}
          rowHeight={this.cache.rowHeight}
          rowRenderer={this.rowRenderer}
          width={width}
          height={height}
          overscanRowCount={10}
          style={{paddingBottom: 50}}
        />
      </div>
    );
  }
}

class AutoSizer extends React.Component<{
  children: (size: {width: number; height: number}) => React.ReactNode;
}> {
  state = {
    width: 0,
    height: 0,
  };

  resizeObserver: any | undefined;

  componentDidMount() {
    this.measure();

    // eslint-disable-next-line react/no-find-dom-node
    const el = ReactDOM.findDOMNode(this);
    if (el && el instanceof HTMLElement && 'ResizeObserver' in window) {
      const RO = window['ResizeObserver'] as any;
      this.resizeObserver = new RO((entries: any) => {
        this.setState({
          width: entries[0].contentRect.width,
          height: entries[0].contentRect.height,
        });
      });
      this.resizeObserver.observe(el);
    }
  }

  componentDidUpdate() {
    this.measure();
  }

  componentWillUnmount() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
  }

  measure() {
    // eslint-disable-next-line react/no-find-dom-node
    const el = ReactDOM.findDOMNode(this);
    if (!el || !(el instanceof HTMLElement)) {
      return;
    }
    if (el.clientWidth !== this.state.width || el.clientHeight !== this.state.height) {
      this.setState({width: el.clientWidth, height: el.clientHeight});
    }
  }

  render() {
    return <div style={{width: '100%', height: '100%'}}>{this.props.children(this.state)}</div>;
  }
}

const ListEmptyState = styled.div`
  z-index: 100;
  position: absolute;
  width: 100%;
  height: calc(100% - 50px);
`;
