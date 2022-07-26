import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';

import {PipelineRoot} from './PipelineRoot';

jest.mock('./GraphExplorer', () => ({
  ...jest.requireActual('./GraphExplorer'),

  // Mock `GraphExplorer` so that we don't actually try to render the DAG.
  GraphExplorer: () => <div />,
}));

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../graph/asyncGraphLayout', () => ({}));

const REPO_NAME = 'foo';
const REPO_LOCATION = 'bar';
const PIPELINE_NAME = 'pipez';

describe('PipelineRoot', () => {
  const mocks = {
    Pipeline: () => ({
      id: () => PIPELINE_NAME,
      modes: () => [...new Array(1)],
      isAssetJob: () => false,
    }),
    SolidDefinition: () => ({
      assetNodes: () => [],
    }),
    PipelineSnapshot: () => ({
      runs: () => [],
      schedules: () => [],
      sensors: () => [],
      solidHandle: null,
    }),
    RepositoryLocation: () => ({
      id: REPO_LOCATION,
      name: REPO_LOCATION,
      repositories: () => [...new Array(1)],
    }),
    Repository: () => ({
      id: REPO_NAME,
      name: REPO_NAME,
      pipelines: () => [...new Array(1)],
      assetGroups: () => [...new Array(0)],
    }),
  };

  const apolloProps = {mocks};

  const repoAddress = buildRepoAddress(REPO_NAME, REPO_LOCATION);
  const pipelineName = 'pipez';
  const path = `/workspace/${repoAddressAsString(repoAddress)}/pipelines/${pipelineName}:default`;

  it('renders overview by default', async () => {
    const routerProps = {
      initialEntries: [path],
    };

    render(
      <TestProvider apolloProps={apolloProps} routerProps={routerProps}>
        <PipelineRoot repoAddress={repoAddress} />
      </TestProvider>,
    );

    await waitFor(() => {
      const selected = screen.getByRole('tab', {selected: true});
      expect(selected.textContent).toMatch(/overview/i);
    });
  });

  describe('Limits Playground based on launch permission', () => {
    it('renders playground route and tab by default', async () => {
      const routerProps = {
        initialEntries: [`${path}/playground`],
      };

      render(
        <TestProvider apolloProps={apolloProps} routerProps={routerProps}>
          <PipelineRoot repoAddress={repoAddress} />
        </TestProvider>,
      );

      await waitFor(() => {
        const selected = screen.getByRole('tab', {selected: true});

        // Route to Playground, verify that the "New run" tab appears.
        expect(selected.textContent).toMatch(/launchpad/i);
        expect(screen.getByText(/new run/i)).toBeVisible();
      });
    });

    it('redirects playground route if no launch permission', async () => {
      const routerProps = {
        initialEntries: [`${path}/playground`],
      };

      render(
        <TestProvider
          permissionOverrides={{
            launch_pipeline_execution: {enabled: false, disabledReason: 'nope'},
          }}
          apolloProps={apolloProps}
          routerProps={routerProps}
        >
          <PipelineRoot repoAddress={repoAddress} />
        </TestProvider>,
      );

      await waitFor(() => {
        const selected = screen.getByRole('tab', {selected: true});

        // Redirect to Definition, which has been highlighted in the tabs.
        expect(selected.textContent).toMatch(/overview/i);

        // Render a disabled "Launchpad" tab.
        expect(screen.queryByRole('tab', {name: /launchpad/i})).toHaveAttribute(
          'aria-disabled',
          'true',
        );
      });
    });
  });
});
