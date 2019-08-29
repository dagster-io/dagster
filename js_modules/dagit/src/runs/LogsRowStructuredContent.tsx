import * as React from "react";
import { Tag, Colors } from "@blueprintjs/core";
import {
  LogsRowStructuredFragment,
  LogsRowStructuredFragment_ExecutionStepFailureEvent,
  LogsRowStructuredFragment_PipelineInitFailureEvent
} from "./types/LogsRowStructuredFragment";
import { EventTypeColumn } from "./LogsRowComponents";
import { MetadataEntries } from "./MetadataEntry";
import { assertUnreachable } from "../Util";
import { MetadataEntryFragment } from "./types/MetadataEntryFragment";

interface IStructuredContentProps {
  node: LogsRowStructuredFragment;
}

export const LogsRowStructuredContent: React.FunctionComponent<
  IStructuredContentProps
> = ({ node }) => {
  switch (node.__typename) {
    // Errors
    case "ExecutionStepFailureEvent":
    case "PipelineInitFailureEvent":
      return <FailureContent node={node} />;

    // Default Behavior
    case "PipelineProcessStartEvent":
      return <DefaultContent message={node.message} eventType="Starting" />;
    case "PipelineProcessStartedEvent":
      return <DefaultContent message={node.message} eventType="Started" />;
    case "ExecutionStepStartEvent":
      return <DefaultContent message={node.message} eventType="Step Start" />;
    case "ExecutionStepSkippedEvent":
      return <DefaultContent message={node.message} eventType="Skipped" />;
    case "ExecutionStepSuccessEvent":
      return (
        <DefaultContent message={node.message} eventType="Step Finished" />
      );
    case "ExecutionStepInputEvent":
      return (
        <DefaultContent
          message={node.message}
          eventType="Input"
          eventIntent={node.typeCheck.success ? "success" : "warning"}
          metadataEntries={node.typeCheck.metadataEntries}
        />
      );
    case "ExecutionStepOutputEvent":
      return (
        <DefaultContent
          message={node.message}
          eventType="Output"
          eventIntent={node.typeCheck.success ? "success" : "warning"}
          metadataEntries={node.typeCheck.metadataEntries}
        />
      );
    case "StepExpectationResultEvent":
      return (
        <DefaultContent
          message={node.message}
          eventType="Expectation"
          eventIntent={node.expectationResult.success ? "success" : "warning"}
          metadataEntries={node.expectationResult.metadataEntries}
        />
      );
    case "StepMaterializationEvent":
      return (
        <DefaultContent
          message={node.message}
          eventType="Materialization"
          metadataEntries={node.materialization.metadataEntries}
        />
      );
    case "ObjectStoreOperationEvent":
      return (
        <DefaultContent
          message={node.message}
          eventType={
            node.operationResult.op === "SET_OBJECT"
              ? "Store"
              : node.operationResult.op === "GET_OBJECT"
              ? "Retrieve"
              : ""
          }
          metadataEntries={node.operationResult.metadataEntries}
        />
      );
    case "PipelineFailureEvent":
    case "PipelineSuccessEvent":
    case "LogMessageEvent":
    case "PipelineStartEvent":
      return <DefaultContent message={node.message} />;

    default:
      // This allows us to check that the switch is exhaustive because the union type should
      // have been narrowed following each successive case to `never` at this point.
      return assertUnreachable(node);
  }
};

// Structured Content Renderers

const DefaultContent: React.FunctionComponent<{
  message: string;
  eventType?: string;
  eventIntent?: "success" | "danger" | "warning";
  metadataEntries?: MetadataEntryFragment[];
}> = ({ message, eventType, eventIntent, metadataEntries }) => {
  return (
    <>
      <EventTypeColumn>
        {eventType && (
          <Tag
            minimal={true}
            intent={eventIntent}
            style={{ fontSize: "0.9em" }}
          >
            {eventType}
          </Tag>
        )}
      </EventTypeColumn>
      <span style={{ flex: 1 }}>
        {message}
        {metadataEntries && metadataEntries.length > 0 && (
          <>
            <br />
            <MetadataEntries entries={metadataEntries} />
          </>
        )}
      </span>
    </>
  );
};

const FailureContent: React.FunctionComponent<{
  node:
    | LogsRowStructuredFragment_ExecutionStepFailureEvent
    | LogsRowStructuredFragment_PipelineInitFailureEvent;
}> = ({ node }) => (
  <>
    <EventTypeColumn>
      <Tag minimal={true} intent="danger" style={{ fontSize: "0.9em" }}>
        Failed
      </Tag>
    </EventTypeColumn>
    <span style={{ flex: 1, color: Colors.RED3 }}>
      {`${node.error.message}\n${node.error.stack}`}
    </span>
  </>
);
