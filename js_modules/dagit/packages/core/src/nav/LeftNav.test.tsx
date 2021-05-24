import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import React from 'react';

import {TestProvider} from '../testing/TestProvider';

import {LeftNav} from './LeftNav';

describe('LeftNav', () => {
  const defaultMocks = {
    WorkspaceOrError: () => ({
      __typename: 'Workspace',
    }),
    Workspace: () => ({
      locationEntries: () => new MockList(2),
    }),
    WorkspaceLocationEntry: () => ({
      locationOrLoadError: {
        __typename: 'RepositoryLocation',
      },
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
        WorkspaceLocationEntry: () => ({
          locationOrLoadError: () => ({
            __typename: 'PythonError',
            message: () => 'error_message',
          }),
        }),
      };

      render(<Test mocks={mocks} />);
      await waitFor(() => {
        expect(screen.getByRole('link', {name: /status warnings found/i})).toBeVisible();
      });
    });
  });
});
