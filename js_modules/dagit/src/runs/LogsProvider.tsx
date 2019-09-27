import * as React from "react";
import { debounce } from "lodash";
import gql from "graphql-tag";
import * as querystring from "query-string";
import { print } from "graphql/language/printer";
import { ApolloClient } from "apollo-client";

import { WEBSOCKET_URI } from "../Util";
import { Run } from "./Run";
import { RunPipelineRunEventFragment } from "./types/RunPipelineRunEventFragment";
import { PipelineRunStatus } from "../types/globalTypes";
import { PipelineRunLogsSubscriptionStatusFragment } from "./types/PipelineRunLogsSubscriptionStatusFragment";
import { PipelineRunLogsSubscription } from "./types/PipelineRunLogsSubscription";

export enum LogLevel {
  DEBUG = "DEBUG",
  INFO = "INFO",
  WARNING = "WARNING",
  ERROR = "ERROR",
  CRITICAL = "CRITICAL",
  EVENT = "EVENT" // structured events
}

export const GetDefaultLogFilter = () => {
  const { q } = querystring.parse(window.location.search);

  return {
    levels: Object.assign(
      Object.keys(LogLevel).reduce(
        (dict, key) => ({ ...dict, [key]: true }),
        {}
      ),
      { [LogLevel.DEBUG]: false }
    ),
    text: typeof q === "string" ? q : "",
    since: 0
  };
};

export interface ILogFilter {
  text: string;
  levels: { [key: string]: boolean };
  since: number;
}

interface ILogsFilterProviderProps {
  client: ApolloClient<any>;
  runId: string;
  filter: ILogFilter;
  children: (props: {
    allNodes: (RunPipelineRunEventFragment & { clientsideKey: string })[];
    filteredNodes: (RunPipelineRunEventFragment & { clientsideKey: string })[];
  }) => React.ReactChild;
}

interface ILogsFilterProviderState {
  nodes: (RunPipelineRunEventFragment & { clientsideKey: string })[];
}

export class LogsProvider extends React.Component<
  ILogsFilterProviderProps,
  ILogsFilterProviderState
> {
  state: ILogsFilterProviderState = {
    nodes: []
  };

  _subscriptionSocket: WebSocket;

  componentDidMount() {
    this.subscribeToRun();
  }

  componentDidUpdate(prevProps: ILogsFilterProviderProps) {
    if (prevProps.runId !== this.props.runId) {
      this.subscribeToRun();
    }
  }

  componentWillUnmount() {
    this.unsubscribeFromRun();
  }

  subscribeToRun() {
    const { runId } = this.props;

    if (this._subscriptionSocket) {
      this.unsubscribeFromRun();
      this.setState({ nodes: [] });
    }

    if (!runId) {
      return;
    }
    const ws = new WebSocket(WEBSOCKET_URI);
    ws.addEventListener("message", e => {
      this.handleWebsocketEvent(JSON.parse(e.data));
    });
    ws.addEventListener("open", () => {
      ws.send(JSON.stringify({ type: "connection_init", payload: {} }));
      ws.send(
        JSON.stringify({
          id: "1",
          type: "start",
          payload: {
            variables: {
              runId: runId,
              after: 0
            },
            extensions: {},
            operationName: "PipelineRunLogsSubscription",
            query: print(PIPELINE_RUN_LOGS_SUBSCRIPTION)
          }
        })
      );
    });

    this._subscriptionSocket = ws;
  }

  unsubscribeFromRun() {
    if (this._subscriptionSocket) {
      this._subscriptionSocket.close();
    }
  }

  updateQueue: PipelineRunLogsSubscription[] = [];

  flushWebsocketUpdates = debounce(() => {
    const nextNodes = [...this.state.nodes];
    let nextPipelineStatus: PipelineRunStatus | null = null;

    for (const update of this.updateQueue) {
      if (
        update.pipelineRunLogs.__typename ===
        "PipelineRunLogsSubscriptionFailure"
      ) {
        break;
      }

      // append the nodes to our local array and give each of them a unique key
      // so we can change the row indexes they're displayed at and still track their
      // sizes, etc.
      nextNodes.push(
        ...update.pipelineRunLogs.messages.map((m, idx) =>
          Object.assign(m, { clientsideKey: `csk${nextNodes.length + idx}` })
        )
      );

      // look for changes to the pipeline's overall run status and sync that to apollo
      for (const { __typename } of update.pipelineRunLogs.messages) {
        if (__typename === "PipelineProcessStartEvent") {
          nextPipelineStatus = PipelineRunStatus.STARTED;
        } else if (__typename === "PipelineSuccessEvent") {
          nextPipelineStatus = PipelineRunStatus.SUCCESS;
        } else if (
          __typename === "PipelineFailureEvent" ||
          __typename === "PipelineInitFailureEvent"
        ) {
          nextPipelineStatus = PipelineRunStatus.FAILURE;
        }
      }
    }

    if (nextPipelineStatus) {
      this.syncPipelineStatusToApolloCache(nextPipelineStatus);
    }
    this.setState({ nodes: nextNodes });
    this.updateQueue = [];
  });

  syncPipelineStatusToApolloCache(status: PipelineRunStatus) {
    const local = this.props.client.readFragment<
      PipelineRunLogsSubscriptionStatusFragment
    >({
      fragmentName: "PipelineRunLogsSubscriptionStatusFragment",
      fragment: PIPELINE_RUN_LOGS_SUBSCRIPTION_STATUS_FRAGMENT,
      id: `PipelineRun.${this.props.runId}`
    });

    if (local) {
      local.status = status;
      this.props.client.writeFragment({
        fragmentName: "PipelineRunLogsSubscriptionStatusFragment",
        fragment: PIPELINE_RUN_LOGS_SUBSCRIPTION_STATUS_FRAGMENT,
        id: `PipelineRun.${this.props.runId}`,
        data: local
      });
    }
  }

  handleWebsocketEvent = (msg: any) => {
    if (msg.type === "data") {
      this.updateQueue.push(msg.payload.data as PipelineRunLogsSubscription);
      this.flushWebsocketUpdates();
    }
  };

  render() {
    const { filter } = this.props;
    const { nodes } = this.state;

    const textLower = filter.text.toLowerCase();

    // step: sum_solid
    const textStep =
      textLower.startsWith("step:") && filter.text.substr(5).trim();

    // type: materialization or type: step start
    const textType =
      textLower.startsWith("type:") &&
      textLower.substr(5).replace(/[ _-]/g, "");

    const filteredNodes = nodes.filter(node => {
      const l = node.__typename === "LogMessageEvent" ? node.level : "EVENT";
      if (!filter.levels[l]) return false;
      if (filter.since && Number(node.timestamp) < filter.since) return false;

      if (textStep) {
        return node.step && node.step.key === textStep;
      } else if (textType) {
        return node.__typename.toLowerCase().includes(textType);
      } else if (textLower) {
        return node.message.toLowerCase().includes(textLower);
      }
      return true;
    });

    return this.props.children({ allNodes: nodes, filteredNodes });
  }
}

export const PIPELINE_RUN_LOGS_SUBSCRIPTION = gql`
  subscription PipelineRunLogsSubscription($runId: ID!, $after: Cursor) {
    pipelineRunLogs(runId: $runId, after: $after) {
      __typename
      ... on PipelineRunLogsSubscriptionSuccess {
        messages {
          ... on MessageEvent {
            runId
          }
          ...RunPipelineRunEventFragment
        }
      }
      ... on PipelineRunLogsSubscriptionFailure {
        missingRunId
        message
      }
    }
  }

  ${Run.fragments.RunPipelineRunEventFragment}
`;

export const PIPELINE_RUN_LOGS_SUBSCRIPTION_STATUS_FRAGMENT = gql`
  fragment PipelineRunLogsSubscriptionStatusFragment on PipelineRun {
    runId
    status
  }
`;
