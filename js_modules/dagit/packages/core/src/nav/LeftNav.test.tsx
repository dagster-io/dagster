import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import React from 'react';

import {TestProvider} from '../testing/TestProvider';

import {LeftNav} from './LeftNav';

jest.mock('./LeftNavRepositorySection', () => ({
  LeftNavRepositorySection: () => null,
}));

describe('LeftNav', () => {
  const defaultMocks = {
    Workspace: () => ({
      locationEntries: () => new MockList(2),
    }),
  };

  const Test: React.FC<{mocks: any}> = ({mocks}) => {
    return (
      <TestProvider apolloProps={{mocks}}>
        <LeftNav />
      </TestProvider>
    );
  };

  it('renders left nav without error', async () => {
    const mocks = {
      Repository: () => ({
        name: () => 'my_repository',
        pipelines: () => new MockList(1),
      }),
      RepositoryLocation: () => ({
        environmentPath: () => 'what then',
        id: () => 'my_location',
        name: () => 'my_location',
        repositories: () => new MockList(1),
      }),
      Workspace: () => ({
        locationEntries: () => new MockList(1),
      }),
      RepositoryOrigin: () => ({
        repositoryName: () => 'my_repository',
        repositoryLocationName: () => 'my_location',
      }),
      SolidDefinition: () => ({
        configField: null,
        description: null,
        inputDefinitions: () => new MockList(1),
        outputDefinitions: () => new MockList(1),
        metadata: () => [],
        name: 'foo_solid',
        requiredResources: () => new MockList(0),
      }),
      SolidInvocationSite: () => ({
        solidHandle: () => ({
          handleID: 'foo_handle',
        }),
      }),
    };

    render(
      <TestProvider
        apolloProps={{mocks}}
        routerProps={{initialEntries: ['/workspace/my_repository@my_location']}}
      >
        <LeftNav />
      </TestProvider>,
    );

    await waitFor(() => {
      const instanceHeader = screen.getByText(/instance/i);
      expect(instanceHeader).toBeVisible();
      const [runsLink] = screen.getAllByText('Runs');
      expect(runsLink.closest('a')).toHaveAttribute('href', '/instance/runs');
      expect(screen.getByText('Assets').closest('a')).toHaveAttribute('href', '/instance/assets');
      expect(screen.getByText('Status').closest('a')).toHaveAttribute('href', '/instance');
    });
  });

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
        RepositoryLocationOrLoadError: () => ({
          __typename: 'PythonError',
          message: () => 'error_message',
        }),
      };

      render(<Test mocks={[defaultMocks, mocks]} />);
      await waitFor(() => {
        expect(screen.getByRole('link', {name: /status warnings found/i})).toBeVisible();
      });
    });
  });
});
