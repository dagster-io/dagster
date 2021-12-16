import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';

import {AppTopNav} from './AppTopNav';

describe('AppTopNav', () => {
  const defaultMocks = {
    Workspace: () => ({
      locationEntries: () => [...new Array(2)],
    }),
  };

  const Test: React.FC<{mocks: any}> = ({mocks}) => {
    return (
      <TestProvider apolloProps={{mocks}}>
        <AppTopNav searchPlaceholder="Test..." />
      </TestProvider>
    );
  };

  it('renders top nav without error', async () => {
    const mocks = {
      Repository: () => ({
        name: () => 'my_repository',
        pipelines: () => [...new Array(1)],
      }),
      RepositoryLocation: () => ({
        environmentPath: () => 'what then',
        id: () => 'my_location',
        name: () => 'my_location',
        repositories: () => [...new Array(1)],
      }),
      Workspace: () => ({
        locationEntries: () => [...new Array(1)],
      }),
      RepositoryOrigin: () => ({
        repositoryName: () => 'my_repository',
        repositoryLocationName: () => 'my_location',
      }),
      SolidDefinition: () => ({
        configField: null,
        description: null,
        inputDefinitions: () => [...new Array(1)],
        outputDefinitions: () => [...new Array(1)],
        metadata: () => [],
        name: 'foo_solid',
        requiredResources: () => [],
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
        <Test mocks={mocks} />
      </TestProvider>,
    );

    await waitFor(() => {
      const runsLink = screen.getByRole('link', {name: /runs/i});
      expect(runsLink.closest('a')).toHaveAttribute('href', '/instance/runs');
      expect(screen.getByText('Assets').closest('a')).toHaveAttribute('href', '/instance/assets');
      expect(screen.getByText('Status').closest('a')).toHaveAttribute('href', '/instance');
    });
  });

  describe('Repo location errors', () => {
    it('does not show warning icon when no errors', async () => {
      render(<Test mocks={defaultMocks} />);
      await waitFor(() => {
        expect(screen.getByText(/workspace/i)).toBeVisible();
        expect(
          screen.queryByRole('img', {
            name: /warning/i,
          }),
        ).toBeNull();
      });
    });

    it.skip('shows the error message when repo location errors are found', async () => {
      const mocks = {
        RepositoryLocationOrLoadError: () => ({
          __typename: 'PythonError',
          message: () => 'error_message',
        }),
      };

      render(<Test mocks={[defaultMocks, mocks]} />);
      await waitFor(() => {
        expect(screen.getByText(/workspace/i)).toBeVisible();
        expect(
          screen.getByRole('img', {
            name: /warning/i,
          }),
        ).toBeVisible();
      });
    });
  });
});
