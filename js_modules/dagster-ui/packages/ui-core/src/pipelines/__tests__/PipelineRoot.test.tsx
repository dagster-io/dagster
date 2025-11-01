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

// Mock useJobPermissions to control job-specific permissions in tests
const mockUseJobPermissions = jest.fn();
jest.mock('../../app/useJobPermissions', () => ({
  useJobPermissions: (...args: any[]) => mockUseJobPermissions(...args),
}));

const REPO_NAME = 'foo';
const REPO_LOCATION = 'bar';

describe('PipelineRoot', () => {
  const repoAddress = buildRepoAddress(REPO_NAME, REPO_LOCATION);
  const pipelineName = 'pipez';
  const path = `/locations/${repoAddressAsURLString(
    repoAddress,
  )}/pipelines/${pipelineName}:default`;

  beforeEach(() => {
    mockUseJobPermissions.mockClear();
  });

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
    // Mock job-specific permissions to return true
    mockUseJobPermissions.mockReturnValue({
      hasLaunchExecutionPermission: true,
      hasLaunchReexecutionPermission: true,
      loading: false,
    });

    render(
      <RecoilRoot>
        <TestPermissionsProvider>
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
    // Mock job-specific permissions to return false
    mockUseJobPermissions.mockReturnValue({
      hasLaunchExecutionPermission: false,
      hasLaunchReexecutionPermission: false,
      loading: false,
    });

    render(
      <RecoilRoot>
        <TestPermissionsProvider>
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
