import {MockLink, MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import {useMemo} from 'react';

import {ApolloClient, ApolloProvider, InMemoryCache} from '../../apollo-client';
import {AppContext} from '../../app/AppContext';
import {
  RELOAD_REPOSITORY_LOCATION_MUTATION,
  REPOSITORY_LOCATION_STATUS_QUERY,
  buildReloadFnForLocation,
  useRepositoryLocationReload,
} from '../useRepositoryLocationReload';

jest.mock('@dagster-io/ui-components', () => ({
  ...jest.requireActual('@dagster-io/ui-components'),
  showToast: jest.fn(),
}));

const LOCATION = 'bar';

const testValue = {
  basePath: '',
  rootServerURI: '',
  telemetryEnabled: false,
};

// -- Mock response builders --

function buildReloadMutationMock(result: Record<string, any>): MockedResponse {
  return {
    request: {
      query: RELOAD_REPOSITORY_LOCATION_MUTATION,
      variables: {location: LOCATION},
    },
    result: {data: {reloadRepositoryLocation: result}},
  };
}

const reloadSuccessMock = () =>
  buildReloadMutationMock({
    __typename: 'WorkspaceLocationEntry',
    id: LOCATION,
    loadStatus: 'LOADED',
    locationOrLoadError: {
      __typename: 'RepositoryLocation',
      id: LOCATION,
    },
  });

function buildStatusQueryResult(
  loadStatus: string,
  locationOrLoadError: Record<string, any> | null = {
    __typename: 'RepositoryLocation',
    id: LOCATION,
    repositories: [],
  },
) {
  return {
    data: {
      workspaceOrError: {
        __typename: 'Workspace',
        id: 'workspace',
        locationEntries: [
          {
            __typename: 'WorkspaceLocationEntry',
            id: LOCATION,
            loadStatus,
            locationOrLoadError,
          },
        ],
      },
    },
  };
}

function buildStatusQueryMock(
  loadStatus: string,
  locationOrLoadError?: Record<string, any> | null,
): MockedResponse {
  return {
    request: {query: REPOSITORY_LOCATION_STATUS_QUERY},
    result: buildStatusQueryResult(loadStatus, locationOrLoadError ?? undefined),
  };
}

const Wrapper = ({children, mocks}: {children: React.ReactNode; mocks: MockedResponse[]}) => (
  <AppContext.Provider value={testValue}>
    <MockedProvider mocks={mocks}>{children}</MockedProvider>
  </AppContext.Provider>
);

describe('useRepositoryReloadLocation', () => {
  const Test = () => {
    const reloadFn = useMemo(() => buildReloadFnForLocation(LOCATION), []);
    const {reloading, error, tryReload} = useRepositoryLocationReload({
      scope: 'location',
      reloadFn,
    });
    return (
      <div>
        <div>{`Reloading: ${reloading}`}</div>
        <div>{`Has error: ${!!error}`}</div>
        <button
          onClick={() => {
            tryReload();
          }}
        >
          Try
        </button>
      </div>
    );
  };

  it('reloads successfully if there are no errors', async () => {
    const user = userEvent.setup();
    render(
      <Wrapper mocks={[reloadSuccessMock(), buildStatusQueryMock('LOADED')]}>
        <Test />
      </Wrapper>,
    );

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    const tryButton = screen.getByRole('button', {name: /try/i});
    await user.click(tryButton);

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: true/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    await waitFor(() => {
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
    });
  });

  it('surfaces mutation errors', async () => {
    const user = userEvent.setup();
    const mutationMock = buildReloadMutationMock({
      __typename: 'RepositoryLocationNotFound',
      message: 'lol not here',
    });

    render(
      <Wrapper mocks={[mutationMock]}>
        <Test />
      </Wrapper>,
    );

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    const tryButton = screen.getByRole('button', {name: /try/i});
    await user.click(tryButton);

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: true/)).toBeVisible();
    });
  });

  it('surfaces code location errors', async () => {
    const user = userEvent.setup();
    const statusMock = buildStatusQueryMock('LOADED', {
      __typename: 'PythonError',
      message: 'u cannot do this',
      stack: [],
      errorChain: [],
    });

    render(
      <Wrapper mocks={[reloadSuccessMock(), statusMock]}>
        <Test />
      </Wrapper>,
    );

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    await user.click(screen.getByText(/Try/));

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: true/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: true/)).toBeVisible();
    });
  });

  // eslint-disable-next-line jest/no-disabled-tests
  it.skip('waits for polling when attempting reload', async () => {
    const user = userEvent.setup();

    // Sequential mocks: first poll returns LOADING, second returns LOADED.
    render(
      <Wrapper
        mocks={[
          reloadSuccessMock(),
          buildStatusQueryMock('LOADING'),
          buildStatusQueryMock('LOADED'),
        ]}
      >
        <Test />
      </Wrapper>,
    );

    await user.click(screen.getByText(/Try/));

    // Still considered reloading while polling occurs.
    await waitFor(() => {
      expect(screen.queryByText(/Reloading: true/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });
  });

  it('stops polling when attempting reload when `LOADED` and there are errors', async () => {
    const user = userEvent.setup();

    const errorLocation = {
      __typename: 'PythonError',
      message: 'u cannot do this',
      stack: [],
      errorChain: [],
    };

    // Create a MockLink directly so we can add responses mid-test.
    const link = new MockLink([reloadSuccessMock(), buildStatusQueryMock('LOADING')]);
    const client = new ApolloClient({link, cache: new InMemoryCache()});

    render(
      <AppContext.Provider value={testValue}>
        <ApolloProvider client={client}>
          <Test />
        </ApolloProvider>
      </AppContext.Provider>,
    );

    await user.click(screen.getByText(/Try/));

    // Still considered reloading while polling occurs (first poll returns LOADING).
    await waitFor(() => {
      expect(screen.queryByText(/Reloading: true/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    // Add the LOADED + error mock and force a refetch.
    link.addMockedResponse(buildStatusQueryMock('LOADED', errorLocation));
    await act(async () => {
      await client.refetchQueries({include: 'active'});
    });

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: true/)).toBeVisible();
    });
  });
});
