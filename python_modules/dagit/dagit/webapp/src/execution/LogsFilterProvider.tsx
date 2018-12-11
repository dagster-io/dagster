import * as React from "react";
import gql from "graphql-tag";
import { LogsFilterProviderMessageFragment } from "./types/LogsFilterProviderMessageFragment";
import { isEqual } from "lodash";

export enum LogLevel {
  DEBUG = "DEBUG",
  INFO = "INFO",
  WARNING = "WARNING",
  ERROR = "ERROR",
  CRITICAL = "CRITICAL"
}

export const DefaultLogFilter = {
  levels: Object.keys(LogLevel).reduce(
    (dict, key) => ({ ...dict, [key]: true }),
    {}
  ),
  text: "",
  since: 0
};

export interface ILogFilter {
  text: string;
  levels: { [key: string]: boolean };
  since: number;
}

interface ILogsFilterProviderProps<T> {
  filter: ILogFilter;
  nodes: T[];
  children: (props: { filteredNodes: T[]; busy: boolean }) => React.ReactChild;
}

interface ILogsFilterProviderState<T> {
  results: T[];
  workCursor: number;
}

export default class LogsFilterProvider<
  T extends LogsFilterProviderMessageFragment
> extends React.Component<
  ILogsFilterProviderProps<T>,
  ILogsFilterProviderState<T>
> {
  static fragments = {
    LogsFilterProviderMessageFragment: gql`
      fragment LogsFilterProviderMessageFragment on PipelineRunEvent {
        ... on MessageEvent {
          message
          timestamp
          level
        }
      }
    `
  };

  state: ILogsFilterProviderState<T> = {
    results: [],
    workCursor: 0
  };

  componentDidMount() {
    this.schedule();
  }

  componentDidUpdate(prevProps: ILogsFilterProviderProps<T>) {
    if (
      prevProps.filter !== this.props.filter ||
      prevProps.nodes !== this.props.nodes
    ) {
      this.setState({ results: [], workCursor: 0 }, () => {
        this.schedule();
      });
    }
  }

  schedule = () => {
    if (isEqual(this.props.filter, DefaultLogFilter)) {
      this.setState({
        results: this.props.nodes,
        workCursor: this.props.nodes.length
      });
      return;
    }

    (window as any).requestIdleCallback(
      (deadline: any) => {
        const { nodes, filter } = this.props;
        const { results, workCursor } = this.state;

        let nextCursor;
        let nextResults = [...results];

        const textLower = filter.text.toLowerCase();

        for (nextCursor = workCursor; nextCursor < nodes.length; nextCursor++) {
          const node = nodes[nextCursor];
          if (deadline.didTimeout) break;
          if (!filter.levels[node.level]) continue;
          if (filter.since && Number(node.timestamp) < filter.since) continue;
          if (filter.text && !node.message.toLowerCase().includes(textLower))
            continue;
          nextResults.push(node);
        }

        this.setState({ results: nextResults, workCursor: nextCursor });

        if (workCursor < nodes.length) {
          this.schedule();
        }
      },
      { timeout: 200 }
    );
  };

  render() {
    const busy = this.state.workCursor !== this.props.nodes.length;
    return this.props.children({ filteredNodes: this.state.results, busy });
  }
}
