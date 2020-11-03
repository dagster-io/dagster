import {MockList} from '@graphql-tools/mock';
import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {useRepositoryOptions} from 'src/DagsterRepositoryContext';
import {RepositoryPicker} from 'src/nav/RepositoryPicker';
import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';
import {asyncWait} from 'src/testing/asyncWait';

describe('RepositoryPicker', () => {
  const defaultMocks = {
    RepositoriesOrError: () => ({
      __typename: 'RepositoryConnection',
      nodes: () => new MockList(2),
    }),
    RepositoryLocation: () => ({
      isReloadSupported: true,
      name: () => 'undisclosed-location',
    }),
  };

  const Wrapper = () => {
    const {loading, options} = useRepositoryOptions();
    return (
      <MemoryRouter>
        <RepositoryPicker
          loading={loading}
          options={options}
          repo={options[0]}
          setRepo={jest.fn()}
        />
      </MemoryRouter>
    );
  };

  it('renders the current repository and refresh button', async () => {
    const mocks = {
      Repository: () => ({
        name: () => 'foo-bar',
      }),
    };

    render(
      <ApolloTestProvider mocks={{...defaultMocks, ...mocks}}>
        <Wrapper />
      </ApolloTestProvider>,
    );

    await asyncWait();
    expect(screen.getByText(/foo-bar/i)).toBeVisible();
    expect(screen.getByRole('button', {name: /refresh/i})).toBeVisible();
  });

  it('surfaces reloading errors', async () => {
    const mocks = {
      ReloadRepositoryLocationMutationResult: () => ({
        __typename: 'RepositoryLocationLoadFailure',
      }),
      PythonError: () => ({
        message: () => 'oh no rofl',
      }),
    };

    render(
      <ApolloTestProvider mocks={{...defaultMocks, ...mocks}}>
        <Wrapper />
      </ApolloTestProvider>,
    );

    await asyncWait();
    userEvent.click(screen.getByRole('button', {name: /refresh/i}));

    await asyncWait();

    // Show error
    const errorText = screen.getByText(/error loading repository/i);
    expect(errorText).toBeVisible();
    userEvent.click(errorText);

    // Show dialog with error message
    expect(screen.getByText(/failed to load repository location/i)).toBeVisible();
    expect(screen.getByText(/oh no rofl/i)).toBeVisible();
  });
});
