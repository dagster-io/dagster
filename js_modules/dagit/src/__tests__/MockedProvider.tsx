import fs from 'fs';

import {ApolloCache} from 'apollo-cache';
import {InMemoryCache as Cache} from 'apollo-cache-inmemory';
import ApolloClient from 'apollo-client';
import {DefaultOptions} from 'apollo-client/ApolloClient';
import * as React from 'react';
import {ApolloProvider} from 'react-apollo';

import {CachedGraphQLRequest, MockLink, MockedResponse} from './MockedApolloLinks';

export interface MockedProviderProps<TSerializedCache = {}> {
  mocks: CachedGraphQLRequest[];
  addTypename?: boolean;
  defaultOptions?: DefaultOptions;
  cache?: ApolloCache<TSerializedCache>;
}

export interface MockedProviderState {
  client: ApolloClient<any>;
}

export class MockedProvider extends React.Component<MockedProviderProps, MockedProviderState> {
  public static defaultProps: MockedProviderProps = {
    mocks: [],
    addTypename: true,
  };

  constructor(props: MockedProviderProps) {
    super(props);

    const {mocks, addTypename, defaultOptions, cache} = this.props;

    const responses: ReadonlyArray<MockedResponse> = mocks.map(
      (mock) =>
        ({
          request: mock,
          result: JSON.parse(fs.readFileSync(mock.filepath).toString()),
        } as MockedResponse),
    );

    const client = new ApolloClient({
      cache: cache || new Cache({addTypename}),
      link: new MockLink(responses, addTypename),
      defaultOptions,
    });

    this.state = {client};
  }

  public render() {
    return <ApolloProvider client={this.state.client}>{this.props.children}</ApolloProvider>;
  }
}
