import * as React from "react";
import gql from "graphql-tag";
import { LogLevel } from "../types/globalTypes";
import { Tag, Colors } from "@blueprintjs/core";

import {
  LogsRowStructuredFragment,
  LogsRowStructuredFragment_ExecutionStepFailureEvent,
  LogsRowStructuredFragment_StepMaterializationEvent,
  LogsRowStructuredFragment_ExecutionStepOutputEvent,
  LogsRowStructuredFragment_ExecutionStepInputEvent,
  LogsRowStructuredFragment_StepExpectationResultEvent,
  LogsRowStructuredFragment_PipelineProcessStartedEvent,
  LogsRowStructuredFragment_PipelineProcessStartEvent,
  LogsRowStructuredFragment_PipelineInitFailureEvent
} from "./types/LogsRowStructuredFragment";
import { LogsRowUnstructuredFragment } from "./types/LogsRowUnstructuredFragment";
import {
  Row,
  StructuredContent,
  EventTypeColumn,
  SolidColumn,
  TimestampColumn
} from "./LogsRowComponents";
import { MetadataEntries, MetadataEntry } from "./MetadataEntry";
import { assertUnreachable } from "../Util";

export class Structured extends React.Component<{
  node: LogsRowStructuredFragment;
}> {
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
          processId
        }
        ... on PipelineProcessStartEvent {
          message
          pipelineName
          runId
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
      }
      ${MetadataEntry.fragments.MetadataEntryFragment}
    `
  };

  renderStructuredContent() {
    const { node } = this.props;

    switch (node.__typename) {
      // Errors
      case "ExecutionStepFailureEvent":
      case "PipelineInitFailureEvent":
        return <DefaultFailureEvent node={node} />;

      // Using custom messages
      case "ExecutionStepStartEvent":
        return (
          <DefaultStructuredEvent
            node={node}
            level={<Tag minimal={true}>Step Start</Tag>}
          />
        );
      case "ExecutionStepSkippedEvent":
        return (
          <DefaultStructuredEvent
            node={node}
            level={<Tag minimal={true}>Skipped</Tag>}
          />
        );
      case "ExecutionStepSuccessEvent":
        return (
          <DefaultStructuredEvent
            node={node}
            level={<Tag minimal={true}>Step Finished</Tag>}
          />
        );

      // Using custom renderers
      case "ExecutionStepInputEvent":
        return <ExecutionStepInputEvent node={node} />;
      case "ExecutionStepOutputEvent":
        return <ExecutionStepOutputEvent node={node} />;
      case "PipelineProcessStartedEvent":
        return <PipelineProcessStartedEvent node={node} />;
      case "PipelineProcessStartEvent":
        return <PipelineProcessStartEvent node={node} />;
      case "StepExpectationResultEvent":
        return <StepExpectationResultEvent node={node} />;
      case "StepMaterializationEvent":
        return <StepMaterializationEvent node={node} />;

      // Using server-provided messages
      case "PipelineFailureEvent":
      case "PipelineProcessStartEvent":
      case "PipelineSuccessEvent":
      case "LogMessageEvent":
      case "PipelineStartEvent":
        return <DefaultStructuredEvent node={node} />;

      default:
        // This allows us to check that the switch is exhaustive because the union type should
        // have been narrowed following each successive case to `never` at this point.
        return assertUnreachable(node);
    }
  }

  render() {
    const { node } = this.props;
    return (
      <Row level={LogLevel.INFO}>
        <SolidColumn stepKey={"step" in node && node.step && node.step.key} />
        <StructuredContent>{this.renderStructuredContent()}</StructuredContent>
        <TimestampColumn time={"timestamp" in node && node.timestamp} />
      </Row>
    );
  }
}

export class Unstructured extends React.Component<{
  node: LogsRowUnstructuredFragment;
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

  render() {
    const { node } = this.props;
    return (
      <Row level={node.level}>
        <SolidColumn stepKey={node.step && node.step.key} />
        <EventTypeColumn>{node.level}</EventTypeColumn>
        <span style={{ flex: 1 }}>{node.message}</span>
        <TimestampColumn time={node.timestamp} />
      </Row>
    );
  }
}

// Structured Content Renderers

const DefaultStructuredEvent: React.FunctionComponent<{
  node: LogsRowStructuredFragment;
  level?: React.ReactNode;
}> = ({ node, level }) => (
  <>
    <EventTypeColumn>{level}</EventTypeColumn>
    <span style={{ flex: 1 }}>{node.message}</span>
  </>
);

const PipelineProcessStartedEvent: React.FunctionComponent<{
  node: LogsRowStructuredFragment_PipelineProcessStartedEvent;
}> = ({ node }) => (
  <>
    <EventTypeColumn>
      <Tag minimal={true}>Started</Tag>
    </EventTypeColumn>
    {`${node.message} `}
  </>
);

const PipelineProcessStartEvent: React.FunctionComponent<{
  node: LogsRowStructuredFragment_PipelineProcessStartEvent;
}> = ({ node }) => (
  <>
    <EventTypeColumn>
      <Tag minimal={true}>Starting</Tag>
    </EventTypeColumn>
    {`${node.message} `}
  </>
);

const DefaultFailureEvent: React.FunctionComponent<{
  node:
    | LogsRowStructuredFragment_ExecutionStepFailureEvent
    | LogsRowStructuredFragment_PipelineInitFailureEvent;
}> = ({ node }) => (
  <>
    <EventTypeColumn>
      <Tag minimal={true} intent="danger">
        Failed
      </Tag>
    </EventTypeColumn>
    <span style={{ flex: 1, color: Colors.RED3 }}>
      {`${node.error.message}\n${node.error.stack}`}
    </span>
  </>
);

const StepExpectationResultEvent: React.FunctionComponent<{
  node: LogsRowStructuredFragment_StepExpectationResultEvent;
}> = ({ node }) => (
  <>
    <EventTypeColumn>
      <Tag
        minimal={true}
        intent={node.expectationResult.success ? "success" : "danger"}
      >
        Expectation
      </Tag>
    </EventTypeColumn>
    <MetadataEntries entries={node.expectationResult.metadataEntries} />
  </>
);

const StepMaterializationEvent: React.FunctionComponent<{
  node: LogsRowStructuredFragment_StepMaterializationEvent;
}> = ({ node }) => (
  <>
    <EventTypeColumn>
      <Tag minimal={true}>Materialization</Tag>
    </EventTypeColumn>
    <MetadataEntries entries={node.materialization.metadataEntries} />
  </>
);

const ExecutionStepOutputEvent: React.FunctionComponent<{
  node: LogsRowStructuredFragment_ExecutionStepOutputEvent;
}> = ({ node }) => {
  return (
    <>
      <EventTypeColumn>
        <Tag
          minimal={true}
          intent={node.typeCheck.success ? "success" : "warning"}
        >
          Output
        </Tag>
      </EventTypeColumn>
      {node.typeCheck.metadataEntries.length ? (
        <MetadataEntries entries={node.typeCheck.metadataEntries} />
      ) : (
        <span style={{ flex: 1 }}>
          No typecheck metadata describing this output.
        </span>
      )}
    </>
  );
};

const ExecutionStepInputEvent: React.FunctionComponent<{
  node: LogsRowStructuredFragment_ExecutionStepInputEvent;
}> = ({ node }) => {
  return (
    <>
      <EventTypeColumn>
        <Tag
          minimal={true}
          intent={node.typeCheck.success ? "success" : "warning"}
        >
          Input
        </Tag>
      </EventTypeColumn>
      {node.typeCheck.metadataEntries.length ? (
        <MetadataEntries entries={node.typeCheck.metadataEntries} />
      ) : (
        <span style={{ flex: 1 }}>
          No typecheck metadata describing this output.
        </span>
      )}
    </>
  );
};
