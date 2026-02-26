import {MockedProvider} from '@apollo/client/testing';
import {render, waitFor} from '@testing-library/react';
import {MemoryRouter, Route, Switch} from 'react-router';

import {__ANONYMOUS_ASSET_JOB_PREFIX} from '../../asset-graph/Utils';
import {
  buildAssetGroup,
  buildPipeline,
  buildRepository,
  buildRepositoryLocation,
  buildWorkspaceLocationEntry,
} from '../../graphql/types';
import {testId} from '../../testing/testId';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {buildWorkspaceMocks} from '../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {BaseFallthroughRoot} from '../BaseFallthroughRoot';
import {
  workspaceWithDunderJob,
  workspaceWithJob,
  workspaceWithNoJobs,
  workspaceWithNoRepos,
} from '../__fixtures__/useJobStateForNav.fixtures';

describe('BaseFallthroughRoot', () => {
  const Test = () => (
    <MemoryRouter initialEntries={[{pathname: '/'}]}>
      <WorkspaceProvider>
        <Switch>
          <Route path="/overview" render={() => <div />} />
          <Route path="/locations" render={() => <div />} />
          <BaseFallthroughRoot />
        </Switch>
        <Route render={(m) => <div data-testid={testId('path')}>{m.location.pathname}</div>} />
        <Route render={(m) => <div data-testid={testId('search')}>{m.location.search}</div>} />
      </WorkspaceProvider>
    </MemoryRouter>
  );

  it('redirects to /locations if there are no repositories', async () => {
    const {getByTestId} = render(
      <MockedProvider mocks={[...workspaceWithNoRepos]}>
        <Test />
      </MockedProvider>,
    );
    await waitFor(() => {
      expect(getByTestId('path').textContent).toEqual('/locations');
    });
  });

  it('redirects to /locations if there are no jobs', async () => {
    const {getByTestId} = render(
      <MockedProvider mocks={[...workspaceWithNoJobs]}>
        <Test />
      </MockedProvider>,
    );
    await waitFor(() => {
      expect(getByTestId('path').textContent).toEqual('/locations');
    });
  });

  it('redirects to /overview without overridden groupBy if repos have visible jobs', async () => {
    const {getByTestId} = render(
      <MockedProvider mocks={[...workspaceWithJob]}>
        <Test />
      </MockedProvider>,
    );
    await waitFor(() => {
      expect(getByTestId('path').textContent).toEqual('/overview');
      expect(getByTestId('search').textContent).toEqual('');
    });
  });

  it('redirects to /overview without overridden groupBy if repos have visible jobs even if asset groups are present', async () => {
    const {getByTestId} = render(
      <MockedProvider
        mocks={buildWorkspaceMocks([
          buildWorkspaceLocationEntry({
            name: 'some_workspace',
            locationOrLoadError: buildRepositoryLocation({
              name: 'location_with_dunder_job',
              repositories: [
                buildRepository({
                  name: `repo_with_pseudo_job`,
                  assetGroups: [
                    buildAssetGroup({
                      groupName: 'group1',
                    }),
                  ],
                  pipelines: [
                    buildPipeline({
                      name: `pseudo_job`,
                      isJob: true,
                    }),
                  ],
                }),
              ],
            }),
          }),
        ])}
      >
        <Test />
      </MockedProvider>,
    );
    await waitFor(() => {
      expect(getByTestId('path').textContent).toEqual('/overview');
      expect(getByTestId('search').textContent).toEqual('');
    });
  });

  it('redirects to /overview grouped by automation if repos have only non-visible jobs', async () => {
    const {getByTestId} = render(
      <MockedProvider mocks={[...workspaceWithDunderJob]}>
        <Test />
      </MockedProvider>,
    );
    await waitFor(() => {
      expect(getByTestId('path').textContent).toEqual('/overview/activity/timeline');
      expect(getByTestId('search').textContent).toEqual('?groupBy=automation');
    });
  });

  it('redirects to /overview grouped by automation if repos have only non-visible jobs even if assetGroups are present', async () => {
    const {getByTestId} = render(
      <MockedProvider
        mocks={buildWorkspaceMocks([
          buildWorkspaceLocationEntry({
            name: 'some_workspace',
            locationOrLoadError: buildRepositoryLocation({
              name: 'location_with_dunder_job',
              repositories: [
                buildRepository({
                  name: `repo_with_pseudo_job`,
                  assetGroups: [
                    buildAssetGroup({
                      groupName: 'group1',
                    }),
                  ],
                  pipelines: [
                    buildPipeline({
                      name: `${__ANONYMOUS_ASSET_JOB_PREFIX}_pseudo_job`,
                      isJob: true,
                    }),
                  ],
                }),
              ],
            }),
          }),
        ])}
      >
        <Test />
      </MockedProvider>,
    );
    await waitFor(() => {
      expect(getByTestId('path').textContent).toEqual('/overview/activity/timeline');
      expect(getByTestId('search').textContent).toEqual('?groupBy=automation');
    });
  });

  it('redirects to the asset graph if there are no jobs but assetGroups are present', async () => {
    const {getByTestId} = render(
      <MockedProvider
        mocks={buildWorkspaceMocks([
          buildWorkspaceLocationEntry({
            name: 'some_workspace',
            locationOrLoadError: buildRepositoryLocation({
              name: 'location_with_dunder_job',
              repositories: [
                buildRepository({
                  name: `repo_with_pseudo_job`,
                  assetGroups: [
                    buildAssetGroup({
                      groupName: 'group1',
                    }),
                  ],
                  pipelines: [],
                }),
              ],
            }),
          }),
        ])}
      >
        <Test />
      </MockedProvider>,
    );
    await waitFor(() => {
      expect(getByTestId('path').textContent).toEqual('/asset-groups');
    });
  });
});
