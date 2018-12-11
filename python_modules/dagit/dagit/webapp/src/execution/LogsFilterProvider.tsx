import * as React from "react";
import gql from "graphql-tag";
import { LogsFilterProviderMessageFragment } from "./types/LogsFilterProviderMessageFragment";

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
  children: (filteredNodes: T[]) => React.ReactChild;
}

export default class LogsFilterProvider<
  T extends LogsFilterProviderMessageFragment
> extends React.Component<ILogsFilterProviderProps<T>> {
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

  render() {
    const { filter, nodes } = this.props;

    let displayed = nodes.filter(node => filter.levels[node.level]);

    if (filter.since > 0) {
      const indexAfter = displayed.findIndex(
        node => Number(node.timestamp) > filter.since
      );
      displayed = indexAfter === -1 ? [] : displayed.slice(indexAfter);
    }
    if (filter.text) {
      displayed = displayed.filter(node => node.message.includes(filter.text));
    }

    return this.props.children(displayed);
  }
}
