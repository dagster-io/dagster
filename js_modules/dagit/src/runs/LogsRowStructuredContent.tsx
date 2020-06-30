import * as React from "react";
import { Tag, Colors, Intent } from "@blueprintjs/core";
import { LogsRowStructuredFragment } from "./types/LogsRowStructuredFragment";
import { EventTypeColumn } from "./LogsRowComponents";
import {
  MetadataEntries,
  createLogRowStructuredContentTable,
  MetadataEntryLink
} from "./MetadataEntry";
import { assertUnreachable } from "../Util";
import { MetadataEntryFragment } from "./types/MetadataEntryFragment";
import { PythonErrorFragment } from "../types/PythonErrorFragment";
import { ComputeLogLink } from "./ComputeLogModal";
import { IRunMetadataDict } from "../RunMetadataProvider";

interface IStructuredContentProps {
  node: LogsRowStructuredFragment;
  metadata: IRunMetadataDict;
}

export const LogsRowStructuredContent: React.FunctionComponent<IStructuredContentProps> = ({
  node,
  metadata
}) => {
  switch (node.__typename) {
    // Errors
    case "PipelineInitFailureEvent":
      return <FailureContent error={node.error} eventType="Pipeline Init Failed" />;
    case "ExecutionStepFailureEvent":
      return (
        <FailureContent
          eventType="Step Failed"
          error={node.error}
          metadataEntries={node?.failureMetadata?.metadataEntries}
        />
      );

    case "ExecutionStepUpForRetryEvent":
      return (
        <DefaultContent
          eventType="Step Requested Retry"
          message={node.message}
          eventIntent="warning"
        />
      );

    case "ExecutionStepStartEvent":
      if (!node.step) {
        return <DefaultContent message={node.message} eventType="Step Start" />;
      } else {
        return (
          <DefaultContent message={node.message} eventType="Step Start">
            {createLogRowStructuredContentTable([
              {
                label: "step_logs",
                item: (
                  <ComputeLogLink
                    stepKey={node.step.key}
                    runState={metadata.steps[node.step.key]?.state}
                  >
                    <MetadataEntryLink>View Raw Step Output</MetadataEntryLink>
                  </ComputeLogLink>
                )
              }
            ])}
          </DefaultContent>
        );
      }
    case "ExecutionStepSkippedEvent":
      return (
        <DefaultContent
          message={node.message}
          eventType="Step Skipped"
          eventColor="rgba(173, 185, 152, 0.3)"
        />
      );

    case "ExecutionStepRestartEvent":
      return <DefaultContent message={node.message} eventType="Step Restart" />;

    case "ExecutionStepSuccessEvent":
      return (
        <DefaultContent message={node.message} eventType="Step Finished" eventIntent="success" />
      );
    case "ExecutionStepInputEvent":
      return (
        <DefaultContent
          message={
            node.message + (node.typeCheck.description ? " " + node.typeCheck.description : "")
          }
          eventType="Input"
          eventIntent={node.typeCheck.success ? "success" : "warning"}
        >
          <MetadataEntries entries={node.typeCheck.metadataEntries} />
        </DefaultContent>
      );
    case "ExecutionStepOutputEvent":
      return (
        <DefaultContent
          message={
            node.message + (node.typeCheck.description ? " " + node.typeCheck.description : "")
          }
          eventType="Output"
          eventIntent={node.typeCheck.success ? "success" : "warning"}
        >
          <MetadataEntries entries={node.typeCheck.metadataEntries} />
        </DefaultContent>
      );
    case "StepExpectationResultEvent":
      return (
        <DefaultContent
          message={node.message}
          eventType="Expectation"
          eventIntent={node.expectationResult.success ? "success" : "warning"}
        >
          <MetadataEntries entries={node.expectationResult.metadataEntries} />
        </DefaultContent>
      );
    case "StepMaterializationEvent":
      return (
        <DefaultContent message={node.message} eventType="Materialization">
          <MetadataEntries entries={node.materialization.metadataEntries} />
        </DefaultContent>
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
        >
          <MetadataEntries entries={node.operationResult.metadataEntries} />
        </DefaultContent>
      );
    case "PipelineFailureEvent":
      return (
        <DefaultContent message={node.message} eventType="Pipeline Failed" eventIntent="danger" />
      );
    case "PipelineSuccessEvent":
      return (
        <DefaultContent
          message={node.message}
          eventType="Pipeline Finished"
          eventIntent="success"
        />
      );

    case "PipelineStartEvent":
      return <DefaultContent message={node.message} eventType="Pipeline Started" />;
    case "EngineEvent":
      if (node.engineError) {
        return <FailureContent error={node.engineError} eventType="Engine Event" />;
      }
      return (
        <DefaultContent
          message={node.message}
          eventType="Engine Event"
          eventColor="rgba(27,164,206,0.2)"
        >
          <MetadataEntries entries={node.metadataEntries} />
        </DefaultContent>
      );
    case "LogMessageEvent":
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
  eventColor?: string;
  eventIntent?: Intent;
  metadataEntries?: MetadataEntryFragment[];
  children?: React.ReactElement;
}> = ({ message, eventType, eventColor, eventIntent, children }) => {
  return (
    <>
      <EventTypeColumn>
        {eventType && (
          <Tag
            minimal={true}
            intent={eventIntent}
            style={
              eventColor
                ? {
                    fontSize: "0.9em",
                    color: "black",
                    background: eventColor
                  }
                : {
                    fontSize: "0.9em"
                  }
            }
          >
            {eventType}
          </Tag>
        )}
      </EventTypeColumn>
      <span style={{ flex: 1 }}>
        {message}
        {children}
      </span>
    </>
  );
};

const FailureContent: React.FunctionComponent<{
  eventType: string;
  error: PythonErrorFragment;
  metadataEntries?: MetadataEntryFragment[];
}> = ({ error, eventType, metadataEntries }) => (
  <>
    <EventTypeColumn>
      <Tag minimal={true} intent="danger" style={{ fontSize: "0.9em" }}>
        {eventType}
      </Tag>
    </EventTypeColumn>
    <span style={{ flex: 1 }}>
      <span style={{ color: Colors.RED3 }}>{`${error.message}`}</span>
      <MetadataEntries entries={metadataEntries} />
      <span style={{ color: Colors.RED3 }}>{`\nStack Trace:\n${error.stack}`}</span>
    </span>
  </>
);
