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

  it('redirects to the asset graph if assetGroups are present and repos have no visible jobs', async () => {
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
      expect(getByTestId('path').textContent).toEqual(
        '/locations/repo_with_pseudo_job@location_with_dunder_job/asset-groups/group1',
      );
    });
  });

  it('redirects to /overview if repos have visible jobs', async () => {
    const {getByTestId} = render(
      <MockedProvider mocks={[...workspaceWithJob]}>
        <Test />
      </MockedProvider>,
    );
    await waitFor(() => {
      expect(getByTestId('path').textContent).toEqual('/overview');
    });
  });

  it('redirects to /locations if repos have no visible jobs and no asset groups', async () => {
    const {getByTestId} = render(
      <MockedProvider mocks={[...workspaceWithDunderJob]}>
        <Test />
      </MockedProvider>,
    );
    await waitFor(() => {
      expect(getByTestId('path').textContent).toEqual('/locations');
    });
  });
});
