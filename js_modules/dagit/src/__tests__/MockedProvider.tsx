import * as React from "react";
import ApolloClient from "apollo-client";
import { DefaultOptions } from "apollo-client/ApolloClient";
import { InMemoryCache as Cache } from "apollo-cache-inmemory";

import { ApolloProvider } from "react-apollo";
import { MockedResponse, MockLink } from "./test-links";
import { ApolloCache } from "apollo-cache";

export interface MockedProviderProps<TSerializedCache = {}> {
  mocks?: Array<MockedResponse>;
  addTypename?: boolean;
  defaultOptions?: DefaultOptions;
  cache?: ApolloCache<TSerializedCache>;
}

export interface MockedProviderState {
  client: ApolloClient<any>;
}

export class MockedProvider extends React.Component<
  MockedProviderProps,
  MockedProviderState
> {
  public static defaultProps: MockedProviderProps = {
    addTypename: true
  };

  constructor(props: MockedProviderProps) {
    super(props);

    const { mocks, addTypename, defaultOptions, cache } = this.props;
    const client = new ApolloClient({
      cache: cache || new Cache({ addTypename }),
      defaultOptions,
      link: new MockLink(mocks || [], addTypename)
    });

    this.state = { client };
  }

  public render() {
    return (
      <ApolloProvider client={this.state.client}>
        {this.props.children}
      </ApolloProvider>
    );
  }

  public componentWillUnmount() {
    if (!this.state.client.queryManager) {
      return;
    }
    const scheduler = this.state.client.queryManager.scheduler;
    Object.keys(scheduler.registeredQueries).forEach(queryId => {
      scheduler.stopPollingQuery(queryId);
    });
    Object.keys(scheduler.intervalQueries).forEach((interval: any) => {
      scheduler.fetchQueriesOnInterval(interval);
    });
  }
}
