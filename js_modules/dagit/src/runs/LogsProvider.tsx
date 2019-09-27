import * as React from "react";
import { throttle } from "lodash";
import * as querystring from "query-string";
import { print } from "graphql/language/printer";
import { ApolloClient } from "apollo-client";

import { PipelineRunLogsSubscription } from "./types/PipelineRunLogsSubscription";
import { RunPipelineRunEventFragment } from "./types/RunPipelineRunEventFragment";
import { PIPELINE_RUN_LOGS_SUBSCRIPTION } from "./Run";
import { WEBSOCKET_URI } from "../Util";

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

  flushWebsocketUpdates = throttle(() => {
    const nextNodes = [...this.state.nodes];
    for (const update of this.updateQueue) {
      if (
        update.pipelineRunLogs.__typename ===
        "PipelineRunLogsSubscriptionFailure"
      ) {
        break;
      }
      nextNodes.push(
        ...update.pipelineRunLogs.messages.map((m, idx) =>
          Object.assign(m, { clientsideKey: `csk${nextNodes.length + idx}` })
        )
      );
    }

    this.setState({ nodes: nextNodes });
    this.updateQueue = [];
  }, 250);

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
