import {render, screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {RecoilRoot} from 'recoil';

import {TestPermissionsProvider} from '../../testing/TestPermissions';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {repoAddressAsURLString} from '../../workspace/repoAddressAsString';
import {PipelineRoot} from '../PipelineRoot';

jest.mock('../../launchpad/LaunchpadAllowedRoot', () => ({
  LaunchpadAllowedRoot: () => <div>launchpad allowed placeholder</div>,
}));

jest.mock('../PipelineOverviewRoot', () => ({
  PipelineOverviewRoot: () => <div>pipeline overview placeholder</div>,
}));

jest.mock('../PipelineOrJobDisambiguationRoot', () => ({
  PipelineOrJobDisambiguationRoot: () => <div>pipeline or job disambiguation placeholder</div>,
}));

jest.mock('../../nav/PipelineNav', () => ({
  ...jest.requireActual('../../nav/PipelineNav'),
  PipelineNav: () => <div />,
}));

jest.mock('../GraphExplorer', () => ({
  ...jest.requireActual('../GraphExplorer'),

  // Mock `GraphExplorer` so that we don't actually try to render the DAG.
  GraphExplorer: () => <div />,
}));

jest.mock('../../app/analytics', () => ({
  ...jest.requireActual('../../app/analytics'),
  useTrackPageView: jest.fn(),
}));

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../graph/asyncGraphLayout', () => ({}));

const REPO_NAME = 'foo';
const REPO_LOCATION = 'bar';

describe('PipelineRoot', () => {
  const repoAddress = buildRepoAddress(REPO_NAME, REPO_LOCATION);
  const pipelineName = 'pipez';
  const path = `/locations/${repoAddressAsURLString(
    repoAddress,
  )}/pipelines/${pipelineName}:default`;

  it('renders overview by default', async () => {
    render(
      <RecoilRoot>
        <MemoryRouter initialEntries={[path]}>
          <PipelineRoot repoAddress={repoAddress} />
        </MemoryRouter>
      </RecoilRoot>,
    );

    const overviewDummy = await screen.findByText(/pipeline overview placeholder/i);
    expect(overviewDummy).toBeVisible();
  });

  it('renders playground route', async () => {
    const locationPermissions = {
      [REPO_LOCATION]: {
        canLaunchPipelineExecution: {enabled: true, disabledReason: ''},
      },
    };

    render(
      <RecoilRoot>
        <TestPermissionsProvider locationOverrides={locationPermissions}>
          <MemoryRouter initialEntries={[`${path}/playground`]}>
            <PipelineRoot repoAddress={repoAddress} />
          </MemoryRouter>
        </TestPermissionsProvider>
      </RecoilRoot>,
    );

    const playgroundDummy = await screen.findByText(/launchpad allowed placeholder/i);
    expect(playgroundDummy).toBeVisible();
  });

  it('redirects to disambiguation if no launch permission', async () => {
    const locationPermissions = {
      [REPO_LOCATION]: {
        canLaunchPipelineExecution: {enabled: false, disabledReason: 'no can do'},
      },
    };

    render(
      <RecoilRoot>
        <TestPermissionsProvider locationOverrides={locationPermissions}>
          <MemoryRouter initialEntries={[`${path}/playground`]}>
            <PipelineRoot repoAddress={repoAddress} />
          </MemoryRouter>
        </TestPermissionsProvider>
      </RecoilRoot>,
    );

    const overviewDummy = await screen.findByText(/pipeline or job disambiguation placeholder/i);
    expect(overviewDummy).toBeVisible();
  });
});
