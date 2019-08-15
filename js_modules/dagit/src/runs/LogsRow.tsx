import * as React from "react";
import gql from "graphql-tag";

import { LogLevel } from "../types/globalTypes";

import { LogsRowStructuredFragment } from "./types/LogsRowStructuredFragment";
import { LogsRowUnstructuredFragment } from "./types/LogsRowUnstructuredFragment";
import {
  Row,
  StructuredContent,
  EventTypeColumn,
  SolidColumn,
  TimestampColumn
} from "./LogsRowComponents";
import { MetadataEntry } from "./MetadataEntry";
import { CellTruncationProvider } from "./CellTruncationProvider";
import { showCustomAlert } from "../CustomAlertProvider";
import LogsRowStructuredContent from "./LogsRowStructuredContent";
import InfoModal from "../InfoModal";
import PythonErrorInfo from "../PythonErrorInfo";

export class Structured extends React.Component<
  {
    node: LogsRowStructuredFragment;
    style: React.CSSProperties;
  },
  {
    expanded: boolean;
  }
> {
  static fragments = {
    LogsRowStructuredFragment: gql`
      fragment LogsRowStructuredFragment on PipelineRunEvent {
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
          message
        }
        ... on PipelineProcessStartEvent {
          message
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
          typeCheck {
            label
            description
            success
            metadataEntries {
              ...MetadataEntryFragment
            }
          }
        }
        ... on ExecutionStepOutputEvent {
          outputName
          typeCheck {
            label
            description
            success
            metadataEntries {
              ...MetadataEntryFragment
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
        ... on ObjectStoreOperationEvent {
          step {
            key
          }
          operationResult {
            op
            metadataEntries {
              ...MetadataEntryFragment
            }
          }
        }
      }
      ${MetadataEntry.fragments.MetadataEntryFragment}
    `
  };

  state = {
    expanded: false
  };

  onExpand = () => {
    this.setState({ expanded: true });
  };

  onCollapse = () => {
    this.setState({ expanded: false });
  };

  renderExpanded() {
    const { node } = this.props;
    const { expanded } = this.state;
    if (!expanded) {
      return null;
    }

    if (
      node.__typename === "ExecutionStepFailureEvent" ||
      node.__typename === "PipelineInitFailureEvent"
    ) {
      return (
        <InfoModal title="Error" onRequestClose={this.onCollapse}>
          <PythonErrorInfo error={node.error} />
        </InfoModal>
      );
    }

    return (
      <InfoModal
        title={(node.step && node.step.key) || undefined}
        onRequestClose={this.onCollapse}
      >
        <StructuredContent>
          <LogsRowStructuredContent node={node} />
        </StructuredContent>
      </InfoModal>
    );
  }

  render() {
    const { node, style } = this.props;
    return (
      <CellTruncationProvider style={style} onExpand={this.onExpand}>
        <Row level={LogLevel.INFO}>
          <SolidColumn stepKey={"step" in node && node.step && node.step.key} />
          <StructuredContent>
            <LogsRowStructuredContent node={node} />
          </StructuredContent>
          <TimestampColumn time={"timestamp" in node && node.timestamp} />
        </Row>
        {this.renderExpanded()}
      </CellTruncationProvider>
    );
  }
}

export class Unstructured extends React.Component<{
  node: LogsRowUnstructuredFragment;
  style: React.CSSProperties;
}> {
  static fragments = {
    LogsRowUnstructuredFragment: gql`
      fragment LogsRowUnstructuredFragment on PipelineRunEvent {
        __typename
        ... on MessageEvent {
          message
          timestamp
          level
          step {
            key
          }
        }
      }
    `
  };

  onExpand = () => {
    showCustomAlert({ message: this.props.node.message, pre: true });
  };

  render() {
    const { node, style } = this.props;
    return (
      <CellTruncationProvider style={style} onExpand={this.onExpand}>
        <Row level={node.level}>
          <SolidColumn stepKey={node.step && node.step.key} />
          <EventTypeColumn>{node.level}</EventTypeColumn>
          <span style={{ flex: 1 }}>{node.message}</span>
          <TimestampColumn time={node.timestamp} />
        </Row>
      </CellTruncationProvider>
    );
  }
}
