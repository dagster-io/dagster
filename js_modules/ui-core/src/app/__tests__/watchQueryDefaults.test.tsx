import {act, renderHook, waitFor} from '@testing-library/react';
import {parse} from 'graphql';
import {ReactNode} from 'react';

import {
  ApolloClient,
  ApolloLink,
  ApolloProvider,
  InMemoryCache,
  Observable,
  useQuery,
} from '../../apollo-client';
import {WATCH_QUERY_DEFAULTS} from '../AppProvider';

// Built with `parse` rather than `gql` so GraphQL codegen doesn't register it as an app query.
const QUERY = parse('query PollTestQuery { version }');

describe('WATCH_QUERY_DEFAULTS', () => {
  let visibility: DocumentVisibilityState = 'visible';

  beforeEach(() => {
    visibility = 'visible';
    jest.spyOn(document, 'visibilityState', 'get').mockImplementation(() => visibility);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('skips pollInterval requests while the document is hidden', async () => {
    let requests = 0;
    const link = new ApolloLink(
      () =>
        new Observable((observer) => {
          requests += 1;
          observer.next({data: {version: String(requests)}});
          observer.complete();
        }),
    );
    const client = new ApolloClient({
      cache: new InMemoryCache(),
      link,
      defaultOptions: {watchQuery: WATCH_QUERY_DEFAULTS},
    });
    const wrapper = ({children}: {children: ReactNode}) => (
      <ApolloProvider client={client}>{children}</ApolloProvider>
    );

    renderHook(() => useQuery(QUERY, {pollInterval: 20}), {wrapper});
    await waitFor(() => expect(requests).toBeGreaterThan(1));

    visibility = 'hidden';
    await act(() => new Promise((resolve) => setTimeout(resolve, 40)));
    const requestsWhenHidden = requests;
    await act(() => new Promise((resolve) => setTimeout(resolve, 150)));
    expect(requests).toBe(requestsWhenHidden);

    visibility = 'visible';
    await waitFor(() => expect(requests).toBeGreaterThan(requestsWhenHidden));
  });
});
