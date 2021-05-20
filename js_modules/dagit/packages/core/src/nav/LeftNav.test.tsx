import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import React from 'react';

import {TestProvider} from '../testing/TestProvider';

import {LeftNav} from './LeftNav';

describe('LeftNav', () => {
  const defaultMocks = {
    RepositoryLocationConnection: () => ({
      nodes: () => new MockList(2),
    }),
  };

  const Test: React.FC<{mocks: any}> = ({mocks}) => {
    return (
      <TestProvider apolloProps={{mocks}}>
        <LeftNav />
      </TestProvider>
    );
  };

  describe('Repo location errors', () => {
    it('does not show warning icon when no errors', async () => {
      render(<Test mocks={defaultMocks} />);
      await waitFor(() => {
        expect(screen.getByRole('link', {name: /status/i})).toBeVisible();
        expect(screen.queryByRole('link', {name: /status warnings found/i})).toBeNull();
      });
    });

    it('shows the error message when repo location errors are found', async () => {
      const mocks = {
        ...defaultMocks,
        RepositoryLocationOrLoadFailure: () => ({
          __typename: 'RepositoryLocationLoadFailure',
        }),
      };

      render(<Test mocks={mocks} />);
      await waitFor(() => {
        expect(screen.getByRole('link', {name: /status warnings found/i})).toBeVisible();
      });
    });
  });
});
