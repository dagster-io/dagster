import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {PERMISSIONS_ALLOW_ALL} from '../app/Permissions';
import {TestProvider} from '../testing/TestProvider';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';

import {PipelineRoot} from './PipelineRoot';

jest.mock('./PipelineExplorer', () => ({
  ...jest.requireActual('./PipelineExplorer'),

  // Mock `PipelineExplorer` so that we don't actually try to render the DAG.
  PipelineExplorer: () => <div />,
}));

const REPO_NAME = 'foo';
const REPO_LOCATION = 'bar';
const PIPELINE_NAME = 'pipez';

describe('PipelineRoot', () => {
  const mocks = {
    Pipeline: () => ({
      id: () => PIPELINE_NAME,
      modes: () => new MockList(1),
    }),
    RepositoryLocation: () => ({
      id: REPO_LOCATION,
      name: REPO_LOCATION,
      repositories: () => new MockList(1),
    }),
    Repository: () => ({
      id: REPO_NAME,
      name: REPO_NAME,
      pipelines: () => new MockList(1),
    }),
  };

  const apolloProps = {mocks};

  const repoAddress = buildRepoAddress(REPO_NAME, REPO_LOCATION);
  const pipelineName = 'pipez';
  const path = `/workspace/${repoAddressAsString(repoAddress)}/pipelines/${pipelineName}:default`;

  it('renders definition by default', async () => {
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
      expect(selected.textContent).toMatch(/definition/i);
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
        expect(selected.textContent).toMatch(/playground/i);
        expect(screen.getByText(/new run/i)).toBeVisible();
      });
    });

    it('redirects playground route if no launch permission', async () => {
      const routerProps = {
        initialEntries: [`${path}/playground`],
      };
      const permissions = {...PERMISSIONS_ALLOW_ALL, launch_pipeline_execution: false};

      render(
        <TestProvider
          appContextProps={{permissions}}
          apolloProps={apolloProps}
          routerProps={routerProps}
        >
          <PipelineRoot repoAddress={repoAddress} />
        </TestProvider>,
      );

      await waitFor(() => {
        const selected = screen.getByRole('tab', {selected: true});

        // Redirect to Definition, which has been highlighted in the tabs.
        expect(selected.textContent).toMatch(/definition/i);

        // Render a disabled "Playground" tab.
        expect(screen.queryByRole('tab', {name: /playground/i})).toHaveAttribute(
          'aria-disabled',
          'true',
        );
      });
    });
  });
});
