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
import { LogsRowStructuredContent } from "./LogsRowStructuredContent";
import InfoModal from "../InfoModal";
import PythonErrorInfo from "../PythonErrorInfo";
import { isEqual } from "apollo-utilities";

interface StructuredProps {
  node: LogsRowStructuredFragment;
  style: React.CSSProperties;
}

interface StructuredState {
  expanded: boolean;
}

export class Structured extends React.Component<
  StructuredProps,
  StructuredState
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
            ...PythonErrorFragment
          }
        }
        ... on ExecutionStepFailureEvent {
          message
          level
          step {
            key
          }
          error {
            ...PythonErrorFragment
          }
          failureMetadata {
            metadataEntries {
              ...MetadataEntryFragment
            }
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
        ... on EngineEvent {
          metadataEntries {
            ...MetadataEntryFragment
          }
          engineError: error {
            ...PythonErrorFragment
          }
        }
      }
      ${MetadataEntry.fragments.MetadataEntryFragment}
      ${PythonErrorInfo.fragments.PythonErrorFragment}
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

    if (node.__typename === "EngineEvent" && node.engineError) {
      return (
        <InfoModal title="Error" onRequestClose={this.onCollapse}>
          <PythonErrorInfo error={node.engineError} />
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
    return (
      <CellTruncationProvider style={this.props.style} onExpand={this.onExpand}>
        <StructuredMemoizedContent node={this.props.node} />
        {this.renderExpanded()}
      </CellTruncationProvider>
    );
  }
}

const StructuredMemoizedContent: React.FunctionComponent<{
  node: LogsRowStructuredFragment;
}> = React.memo(
  ({ node }) => (
    <Row level={LogLevel.INFO}>
      <SolidColumn stepKey={"step" in node && node.step && node.step.key} />
      <StructuredContent>
        <LogsRowStructuredContent node={node} />
      </StructuredContent>
      <TimestampColumn time={"timestamp" in node && node.timestamp} />
    </Row>
  ),
  isEqual
);

interface UnstructuredProps {
  node: LogsRowUnstructuredFragment;
  style: React.CSSProperties;
}

export class Unstructured extends React.Component<UnstructuredProps> {
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
    showCustomAlert({
      body: (
        <div style={{ whiteSpace: "pre-wrap" }}>{this.props.node.message}</div>
      )
    });
  };

  render() {
    return (
      <CellTruncationProvider style={this.props.style} onExpand={this.onExpand}>
        <UnstructuredMemoizedContent node={this.props.node} />
      </CellTruncationProvider>
    );
  }
}

const UnstructuredMemoizedContent: React.FunctionComponent<{
  node: LogsRowUnstructuredFragment;
}> = React.memo(
  ({ node }) => (
    <Row level={node.level}>
      <SolidColumn stepKey={node.step && node.step.key} />
      <EventTypeColumn>{node.level}</EventTypeColumn>
      <span style={{ flex: 1 }}>{node.message}</span>
      <TimestampColumn time={node.timestamp} />
    </Row>
  ),
  isEqual
);
