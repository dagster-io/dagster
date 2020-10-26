import {render, screen} from '@testing-library/react';
import * as React from 'react';

import {App} from 'src/App';
import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';
import {asyncWait} from 'src/testing/asyncWait';

it('renders left nav without error', async () => {
  const mocks = {
    Repository: () => ({
      name: 'my_repository',
    }),
    RepositoriesOrError: () => ({
      __typename: 'RepositoryConnection',
    }),
  };

  render(
    <ApolloTestProvider mocks={mocks}>
      <App />
    </ApolloTestProvider>,
  );

  await asyncWait();

  expect(screen.getByText('Instance Details')).toBeVisible();

  const [runsLink] = screen.getAllByText('Runs');
  expect(runsLink.closest('a')).toHaveAttribute('href', '/instance/runs');
  expect(screen.getByText('Assets').closest('a')).toHaveAttribute('href', '/instance/assets');
  expect(screen.getByText('Scheduler').closest('a')).toHaveAttribute('href', '/instance/scheduler');

  expect(screen.getByText('my_repository')).toBeVisible();
});
