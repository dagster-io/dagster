import {render, screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import {PipelineNav} from '../../nav/PipelineNav';
import {TestPermissionsProvider} from '../../testing/TestPermissions';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';

jest.mock('../../workspace/WorkspaceContext/util', () => ({
  ...jest.requireActual('../../workspace/WorkspaceContext/util'),
  useRepository: jest.fn(() => null),
}));

jest.mock('../../nav/JobMetadata', () => ({
  JobMetadata: () => <div />,
}));

jest.mock('../../nav/RepositoryLink', () => ({
  RepositoryLink: () => <div />,
}));

// We don't actually want to import the PipelineOverviewRoot via context fallthrough.
jest.mock('../PipelineOverviewRoot', () => ({
  PipelineOverviewRoot: () => <div />,
}));

describe('PipelineNav', () => {
  const repoAddress = buildRepoAddress('bar', 'baz');

  it('enables launchpad tab if not permissioned', async () => {
    const locationOverrides = {
      baz: {
        canLaunchPipelineExecution: {enabled: true, disabledReason: ''},
      },
    };

    render(
      <TestPermissionsProvider locationOverrides={locationOverrides}>
        <MemoryRouter initialEntries={['/locations/bar@baz/jobs/foo/overview']}>
          <PipelineNav repoAddress={repoAddress} />
        </MemoryRouter>
      </TestPermissionsProvider>,
    );

    const launchpadTab = await screen.findByRole('tab', {name: /launchpad/i});
    expect(launchpadTab).toHaveAttribute('aria-disabled', 'false');
  });

  it('disables launchpad tab if not permissioned', async () => {
    const locationOverrides = {
      baz: {
        canLaunchPipelineExecution: {enabled: false, disabledReason: 'nope'},
      },
    };

    render(
      <TestPermissionsProvider locationOverrides={locationOverrides}>
        <MemoryRouter initialEntries={['/locations/bar@baz/jobs/foo/overview']}>
          <PipelineNav repoAddress={repoAddress} />
        </MemoryRouter>
      </TestPermissionsProvider>,
    );

    const launchpadTab = await screen.findByRole('tab', {name: /launchpad/i});
    expect(launchpadTab).toHaveAttribute('aria-disabled', 'true');
  });
});
