import {Colors, NonIdealState, Spinner} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import gql from 'graphql-tag';
import * as React from 'react';
import * as ReactDOM from 'react-dom';
import {CellMeasurer, CellMeasurerCache, List, ListRowProps} from 'react-virtualized';
import styled from 'styled-components/macro';

import {IRunMetadataDict} from '../RunMetadataProvider';

import * as LogsRow from './LogsRow';
import {ColumnWidthsProvider, Headers} from './LogsScrollingTableHeader';
import {LogsScrollingTableMessageFragment} from './types/LogsScrollingTableMessageFragment';

interface ILogsScrollingTableProps {
  nodes?: (LogsScrollingTableMessageFragment & {clientsideKey: string})[];
  loading: boolean;

  // We use this string to know whether the changes to `nodes` require us to
  // re-layout the entire table. Appending new rows can be done very fast, but
  // removing some rows requires the whole list be "reflowed" again. Checking
  // `nodes` for equality doesn't let us optimize for the append- case.
  filterKey: string;

  metadata: IRunMetadataDict;
}

interface ILogsScrollingTableSizedProps extends ILogsScrollingTableProps {
  width: number;
  height: number;
}

export default class LogsScrollingTable extends React.Component<ILogsScrollingTableProps> {
  static fragments = {
    LogsScrollingTableMessageFragment: gql`
      fragment LogsScrollingTableMessageFragment on PipelineRunEvent {
        __typename
        ...LogsRowStructuredFragment
        ...LogsRowUnstructuredFragment
      }

      ${LogsRow.Structured.fragments.LogsRowStructuredFragment}
      ${LogsRow.Unstructured.fragments.LogsRowUnstructuredFragment}
    `,
  };

  table = React.createRef<LogsScrollingTableSized>();

  render() {
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
                {...this.props}
              />
            )}
          </AutoSizer>
        </div>
      </ColumnWidthsProvider>
    );
  }
}

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
    keyMapper: (rowIndex) => (this.props.nodes ? this.props.nodes[rowIndex].clientsideKey : ''),
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

  rowRenderer = ({parent, index, style}: ListRowProps) => {
    if (!this.props.nodes) {
      return;
    }
    const node = this.props.nodes[index];
    const metadata = this.props.metadata;
    if (!node) {
      return <span />;
    }
    const isLastRow = index === this.props.nodes.length - 1;
    const lastRowStyles = isLastRow
      ? {
          borderBottom: `1px solid ${Colors.LIGHT_GRAY3}`,
        }
      : {};

    return (
      <CellMeasurer cache={this.cache} index={index} parent={parent} key={node.clientsideKey}>
        {node.__typename === 'LogMessageEvent' ? (
          <LogsRow.Unstructured
            node={node}
            style={{...style, width: this.props.width, ...lastRowStyles}}
          />
        ) : (
          <LogsRow.Structured
            node={node}
            metadata={metadata}
            style={{...style, width: this.props.width, ...lastRowStyles}}
          />
        )}
      </CellMeasurer>
    );
  };

  noContentRenderer = () => {
    if (this.props.nodes) {
      return <NonIdealState icon={IconNames.CONSOLE} title="No logs to display" />;
    }
    return <span />;
  };

  render() {
    return (
      <div onScroll={this.onScroll}>
        {this.props.loading && (
          <ListEmptyState>
            <NonIdealState icon={<Spinner size={24} />} title="Fetching logs..." />
          </ListEmptyState>
        )}
        <List
          ref={this.list}
          deferredMeasurementCache={this.cache}
          rowCount={this.props.nodes ? this.props.nodes.length : 0}
          noContentRenderer={this.noContentRenderer}
          rowHeight={this.cache.rowHeight}
          rowRenderer={this.rowRenderer}
          width={this.props.width}
          height={this.props.height}
          overscanRowCount={10}
          style={{paddingBottom: 100}}
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
