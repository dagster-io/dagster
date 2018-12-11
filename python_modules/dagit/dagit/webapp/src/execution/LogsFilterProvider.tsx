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
    results: []
  };

  componentDidMount() {
    this.runFilter();
  }

  componentDidUpdate(prevProps: ILogsFilterProviderProps<T>) {
    if (
      prevProps.filter !== this.props.filter ||
      prevProps.nodes !== this.props.nodes
    ) {
      this.runFilter();
    }
  }

  runFilter = () => {
    const { nodes, filter } = this.props;

    if (isEqual(filter, DefaultLogFilter)) {
      this.setState({ results: nodes });
      return;
    }

    let nextResults = [];

    const textLower = filter.text.toLowerCase();

    for (let nextCursor = 0; nextCursor < nodes.length; nextCursor++) {
      const node = nodes[nextCursor];
      if (!filter.levels[node.level]) continue;
      if (filter.since && Number(node.timestamp) < filter.since) continue;
      if (filter.text && !node.message.toLowerCase().includes(textLower))
        continue;
      nextResults.push(node);
    }

    this.setState({ results: nextResults });
  };

  render() {
    return this.props.children({
      filteredNodes: this.state.results,
      busy: false
    });
  }
}
