import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {OnReload} from 'src/nav/ReloadRepositoryLocationButton';
import {RepositoryPicker} from 'src/nav/RepositoryPicker';
import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';
import {useRepositoryOptions, WorkspaceProvider} from 'src/workspace/WorkspaceContext';

describe('RepositoryPicker', () => {
  const defaultMocks = {
    RepositoryLocationOrLoadFailure: () => ({
      __typename: 'RepositoryLocation',
    }),
    RepositoryLocationsOrError: () => ({
      __typename: 'RepositoryLocationConnection',
    }),
    RepositoryLocationConnection: () => ({
      nodes: () => new MockList(1),
    }),
    RepositoryLocation: () => ({
      isReloadSupported: true,
      name: () => 'undisclosed-location',
      repositories: () => new MockList(1),
    }),
  };

  const Test: React.FC<{onReload?: OnReload}> = (props) => {
    const {loading, options} = useRepositoryOptions();
    return (
      <RepositoryPicker
        loading={loading}
        onReload={props.onReload || jest.fn()}
        options={options}
        repo={options[0]}
      />
    );
  };

  const Wrapper: React.FC<{mocks: any; onReload?: OnReload}> = (props) => {
    const {mocks, onReload} = props;
    return (
      <MemoryRouter>
        <ApolloTestProvider mocks={mocks}>
          <WorkspaceProvider>
            <Test onReload={onReload} />
          </WorkspaceProvider>
        </ApolloTestProvider>
      </MemoryRouter>
    );
  };

  it('renders the current repository and refresh button', async () => {
    const mocks = {
      ...defaultMocks,
      Repository: () => ({
        name: () => 'foo-bar',
      }),
    };

    render(<Wrapper mocks={mocks} />);

    await waitFor(() => {
      expect(screen.getByText(/foo-bar/i)).toBeVisible();
      expect(screen.getByRole('button', {name: /refresh/i})).toBeVisible();
    });
  });

  it('surfaces reloading errors', async () => {
    const mocks = {
      ...defaultMocks,
      ReloadRepositoryLocationMutationResult: () => ({
        __typename: 'RepositoryLocationLoadFailure',
      }),
      PythonError: () => ({
        message: () => 'oh no rofl',
      }),
    };

    const onReload = jest.fn();

    render(<Wrapper mocks={mocks} onReload={onReload} />);

    const button = await screen.findByRole('button', {name: /refresh/i});
    userEvent.click(button);

    await waitFor(() => {
      expect(onReload.mock.calls.length).toBe(1);
      expect(onReload.mock.calls[0]).toEqual([
        'undisclosed-location',
        {type: 'error', message: 'oh no rofl'},
      ]);
    });
  });
});
