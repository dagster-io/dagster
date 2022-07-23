import {fireEvent, render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';

import {buildReloadFnForLocation, useRepositoryLocationReload} from './useRepositoryLocationReload';

describe('useRepositoryReloadLocation', () => {
  jest.useFakeTimers();

  const LOCATION = 'bar';

  const defaultMocks = {
    WorkspaceLocationEntry: () => ({
      id: () => LOCATION,
      name: () => LOCATION,
      loadStatus: () => 'LOADED',
    }),
    ReloadRepositoryLocationMutationResult: () => ({
      __typename: 'WorkspaceLocationEntry',
    }),
    RepositoryLocation: () => ({
      id: () => LOCATION,
    }),
  };

  const Test = () => {
    const reloadFn = React.useMemo(() => buildReloadFnForLocation(LOCATION), []);
    const {reloading, error, tryReload} = useRepositoryLocationReload({
      scope: 'location',
      reloadFn,
    });
    return (
      <div>
        <div>{`Reloading: ${reloading}`}</div>
        <div>{`Has error: ${!!error}`}</div>
        <button onClick={() => tryReload()}>Try</button>
      </div>
    );
  };

  it('reloads successfully if there are no errors', async () => {
    render(
      <TestProvider apolloProps={{mocks: [defaultMocks]}}>
        <Test />
      </TestProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    fireEvent.click(screen.getByText(/Try/));

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: true/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    jest.runAllTicks();

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });
  });

  it('surfaces mutation errors', async () => {
    const mocks = {
      ReloadRepositoryLocationMutationResult: () => ({
        __typename: 'RepositoryLocationNotFound',
        message: () => 'lol not here',
      }),
    };

    render(
      <TestProvider apolloProps={{mocks: [defaultMocks, mocks]}}>
        <Test />
      </TestProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    fireEvent.click(screen.getByText(/Try/));

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: true/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    jest.runAllTicks();

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: true/)).toBeVisible();
    });
  });

  it('surfaces repository location errors', async () => {
    const mocks = {
      RepositoryLocationOrLoadError: () => ({
        __typename: 'PythonError',
        message: () => 'u cannot do this',
      }),
    };

    render(
      <TestProvider apolloProps={{mocks: [defaultMocks, mocks]}}>
        <Test />
      </TestProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    fireEvent.click(screen.getByText(/Try/));

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: true/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    jest.runAllTicks();

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: true/)).toBeVisible();
    });
  });

  it('waits for polling when attempting reload', async () => {
    const mocks = {
      WorkspaceLocationEntry: () => ({
        id: () => LOCATION,
        name: () => LOCATION,
        loadStatus: () => 'LOADING',
      }),
    };

    const {rerender} = render(
      <TestProvider apolloProps={{mocks: [defaultMocks, mocks]}}>
        <Test />
      </TestProvider>,
    );

    fireEvent.click(screen.getByText(/Try/));
    jest.runAllTicks();

    // Still considered reloading while polling occurs.
    await waitFor(() => {
      expect(screen.queryByText(/Reloading: true/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    jest.runAllTicks();

    // Still polling.
    await waitFor(() => {
      expect(screen.queryByText(/Reloading: true/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    // Set the location entry to `LOADED`, which should terminate polling.
    rerender(
      <TestProvider apolloProps={{mocks: defaultMocks}}>
        <Test />
      </TestProvider>,
    );

    jest.runAllTicks();

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });
  });

  it('stops polling when attempting reload when `LOADED` and there are errors', async () => {
    const mocks = {
      WorkspaceLocationEntry: () => ({
        id: () => LOCATION,
        name: () => LOCATION,
        loadStatus: () => 'LOADING',
      }),
    };

    const {rerender} = render(
      <TestProvider apolloProps={{mocks: [defaultMocks, mocks]}}>
        <Test />
      </TestProvider>,
    );

    fireEvent.click(screen.getByText(/Try/));
    jest.runAllTicks();

    // Still considered reloading while polling occurs.
    await waitFor(() => {
      expect(screen.queryByText(/Reloading: true/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    jest.runAllTicks();

    // Still polling.
    await waitFor(() => {
      expect(screen.queryByText(/Reloading: true/)).toBeVisible();
      expect(screen.queryByText(/Has error: false/)).toBeVisible();
    });

    const mocksWithError = {
      RepositoryLocationOrLoadError: () => ({
        __typename: 'PythonError',
        message: () => 'u cannot do this',
      }),
    };

    // Set an error on the repository location and use the `LOADED` state from the
    // default mocks to end polling.
    rerender(
      <TestProvider apolloProps={{mocks: [defaultMocks, mocksWithError]}}>
        <Test />
      </TestProvider>,
    );

    jest.runAllTicks();

    await waitFor(() => {
      expect(screen.queryByText(/Reloading: false/)).toBeVisible();
      expect(screen.queryByText(/Has error: true/)).toBeVisible();
    });
  });
});
