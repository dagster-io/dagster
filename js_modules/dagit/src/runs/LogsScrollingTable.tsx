import * as React from "react";
import * as ReactDOM from "react-dom";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, NonIdealState, Tag } from "@blueprintjs/core";
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
import { showCustomAlert } from "../CustomAlertProvider";
import { DisplayEvent } from "src/DisplayEvent";
import { extractMetadataFromLogs } from "src/RunMetadataProvider";
import { highlightBlock } from "highlight.js";
import "highlight.js/styles/xcode.css";

class HighlightedBlock extends React.Component<{ value: string }> {
  _el = React.createRef<HTMLPreElement>();

  componentDidMount() {
    if (this._el.current) highlightBlock(this._el.current);
  }

  render() {
    const { value, ...rest } = this.props;
    return (
      <pre ref={this._el} {...rest}>
        {value}
      </pre>
    );
  }
}

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

function textForLog(log: LogsScrollingTableMessageFragment) {
  if (
    log.__typename === "ExecutionStepFailureEvent" ||
    log.__typename === "PipelineInitFailureEvent"
  ) {
    return `${log.message}\n${log.error.message}\n${log.error.stack}`;
  }
  return log.message;
}

function styleValueRepr(repr: string) {
  if (repr.startsWith("DataFrame")) {
    const content = repr.split("[")[1].split("]")[0];
    const cells: React.ReactNode[] = [];
    content.split(",").forEach(el => {
      const [key, val] = el.split(":");
      cells.push(
        <React.Fragment key={key}>
          <span style={{ color: "#bd4e08" }}>{key}:</span>
          <span style={{ color: "purple" }}>{val}</span>,
        </React.Fragment>
      );
    });
    return <span>DataFrame: [{cells}]</span>;
  }
  if (repr.startsWith("<dagster")) {
    return <span style={{ color: "#bd4e08" }}>{repr}</span>;
  }
  if (repr.startsWith("{'")) {
    return (
      <HighlightedBlock
        value={JSON.stringify(
          JSON.parse(repr.replace(/"/g, "'").replace(/'/g, '"')),
          null,
          2
        )}
      />
    );
  }
  return repr;
}

export default class LogsScrollingTable extends React.Component<
  ILogsScrollingTableProps
> {
  static fragments = {
    LogsScrollingTableMessageFragment: gql`
      fragment MetadataEntryFragment on EventMetadataEntry {
        label
        description
        ... on EventPathMetadataEntry {
          path
        }
        ... on EventJsonMetadataEntry {
          jsonString
        }
        ... on EventUrlMetadataEntry {
          url
        }
        ... on EventTextMetadataEntry {
          text
        }
      }
      fragment LogsScrollingTableMessageFragment on PipelineRunEvent {
        __typename
        ... on MessageEvent {
          message
          timestamp
          level
          step {
            key
          }
        }
        ... on PipelineProcessStartedEvent {
          processId
        }
        ... on StepMaterializationEvent {
          step {
            key
          }
          materialization {
            label
            description
            metadataEntries {
              ...MetadataEntryFragment
            }
          }
        }
        ... on PipelineInitFailureEvent {
          error {
            stack
            message
          }
        }
        ... on ExecutionStepFailureEvent {
          message
          level
          step {
            key
          }
          error {
            stack
            message
          }
        }
        ... on ExecutionStepInputEvent {
          inputName
          valueRepr
          typeCheck {
            label
            description
            success
            metadataEntries {
              label
              description
            }
          }
        }
        ... on ExecutionStepOutputEvent {
          outputName
          valueRepr
          typeCheck {
            label
            description
            success
            metadataEntries {
              label
              description
            }
          }
        }
        ... on StepExpectationResultEvent {
          expectationResult {
            success
            label
            description
            metadataEntries {
              ...MetadataEntryFragment
            }
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

  cellContent = (rowIndex: number) => {
    if (!this.props.nodes) return;
    const node = this.props.nodes[rowIndex];
    if (!node) return <span />;

    if (node.__typename === "StepExpectationResultEvent") {
      const events = extractMetadataFromLogs([node]);
      return (
        <div>
          {events.steps[node.step!.key].expectationResults.map((e, idx) => (
            <DisplayEvent event={e} key={`${idx}`} />
          ))}
        </div>
      );
    }
    if (node.__typename === "StepMaterializationEvent") {
      const events = extractMetadataFromLogs([node]);
      return (
        <div>
          {events.steps[node.step!.key].materializations.map((e, idx) => (
            <DisplayEvent event={e} key={`${idx}`} />
          ))}
        </div>
      );
    }
    if (node.__typename === "ExecutionStepStartEvent") {
      return <span>Started</span>;
    }
    if (node.__typename === "ExecutionStepFailureEvent") {
      return (
        <span>{`Failed with error: \n${node.error.message}\n${
          node.error.stack
        }`}</span>
      );
    }
    if (node.__typename === "ExecutionStepSkippedEvent") {
      return <span>Skipped</span>;
    }
    if (node.__typename === "ExecutionStepOutputEvent") {
      return (
        <span>
          <Tag
            minimal={true}
            intent={node.typeCheck.success ? "success" : "warning"}
            style={{ marginRight: 4 }}
          >
            Output
          </Tag>
          {node.outputName}: {styleValueRepr(node.valueRepr)}
        </span>
      );
    }
    if (node.__typename === "ExecutionStepInputEvent") {
      return (
        <span>
          <Tag
            minimal={true}
            intent={node.typeCheck.success ? "success" : "warning"}
            style={{ marginRight: 4 }}
          >
            Input
          </Tag>
          {node.inputName}: {styleValueRepr(node.valueRepr)}
        </span>
      );
    }
    if (node.__typename === "ExecutionStepSuccessEvent") {
      return <span>Success</span>;
    }
    return textForLog(node);
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
    const width = this.columnWidth({ index: columnIndex });

    let content = null;

    switch (columnIndex) {
      case 0:
        content = (
          <Cell style={{ ...style, width }} level={node.level}>
            {node.level}
          </Cell>
        );
        break;
      case 1:
        content = (
          <Cell style={{ ...style, width }} level={node.level}>
            {node.step ? node.step.key : ""}
          </Cell>
        );
        break;
      case 2:
        content = (
          <OverflowDetectingCell style={{ ...style, width }} level={node.level}>
            {this.cellContent(rowIndex)}
          </OverflowDetectingCell>
        );
        break;
      case 3:
        content = (
          <Cell
            style={{ ...style, width, textAlign: "right" }}
            level={node.level}
          >
            {new Date(Number(node.timestamp))
              .toISOString()
              .replace("Z", "")
              .split("T")
              .pop()}
          </Cell>
        );
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
        {content}
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

  columnWidth = ({ index }: { index: number }) => {
    switch (index) {
      case 0:
        return 80;
      case 1:
        return 320;
      case 2:
        return this.props.width - 110 - 320 - 80;
      case 3:
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
          columnCount={4}
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

const Cell = styled.div<{ level: LogLevel }>`
  font-size: 0.85em;
  width: 100%;
  height: 100%;
  max-height: 17em;
  overflow-y: hidden;
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

const OverflowFade = styled.div<{ level: LogLevel }>`
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  user-select: none;
  pointer-events: none;
  background: linear-gradient(
    to bottom,
    ${props =>
        ({
          [LogLevel.DEBUG]: `rgba(245, 248, 250, 0)`,
          [LogLevel.INFO]: `rgba(245, 248, 250, 0)`,
          [LogLevel.WARNING]: `rgba(240, 241, 237, 0)`,
          [LogLevel.ERROR]: `rgba(243, 236, 239, 0)`,
          [LogLevel.CRITICAL]: `rgba(243, 236, 239, 0)`
        }[props.level])}
      0%,
    ${props =>
        ({
          [LogLevel.DEBUG]: `rgba(245, 248, 250, 255)`,
          [LogLevel.INFO]: `rgba(245, 248, 250, 255)`,
          [LogLevel.WARNING]: `rgba(240, 241, 237, 255)`,
          [LogLevel.ERROR]: `rgba(243, 236, 239, 255)`,
          [LogLevel.CRITICAL]: `rgba(243, 236, 239, 255)`
        }[props.level])}
      100%
  );
`;
const OverflowBanner = styled.div`
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  user-select: none;
  background: ${Colors.LIGHT_GRAY3};
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
  padding: 2px 12px;
  color: ${Colors.BLACK};
  &:hover {
    color: ${Colors.BLACK};
    background: ${Colors.LIGHT_GRAY1};
  }
`;

class OverflowDetectingCell extends React.Component<
  {
    level: LogLevel;
    style: React.CSSProperties;
  },
  { isOverflowing: boolean }
> {
  state = {
    isOverflowing: false
  };
  componentDidMount() {
    this.detectOverflow();
  }

  componentDidUpdate() {
    this.detectOverflow();
  }

  detectOverflow() {
    const el = ReactDOM.findDOMNode(this);
    if (!(el && "clientHeight" in el)) return;

    const isOverflowing = el.scrollHeight > this.props.style.height!;
    if (isOverflowing !== this.state.isOverflowing) {
      this.setState({ isOverflowing });
    }
  }

  onView = () => {
    const el = ReactDOM.findDOMNode(this) as HTMLElement;
    const message = el.firstChild && el.firstChild.textContent;
    if (!message) return;
    showCustomAlert({ message: message, pre: true });
  };

  render() {
    const { level, style } = this.props;

    return (
      <Cell style={style} level={level}>
        {this.props.children}
        {this.state.isOverflowing && (
          <>
            <OverflowFade level={level} />
            <OverflowBanner onClick={this.onView}>
              View Full Message
            </OverflowBanner>
          </>
        )}
      </Cell>
    );
  }
}
