import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';

import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {useJobStateForNav} from '../AppTopNav/useJobStateForNav';
import {
  workspaceWithDunderJob,
  workspaceWithJob,
  workspaceWithNoJobs,
} from '../__fixtures__/useJobStateForNav.fixtures';

describe('useJobStateForNav', () => {
  const Test = () => {
    const value = useJobStateForNav();
    return <div>{value}</div>;
  };

  it('returns `unknown` if still loading, then finds jobs and returns `has-jobs`', async () => {
    render(
      <MockedProvider mocks={workspaceWithJob}>
        <WorkspaceProvider>
          <Test />
        </WorkspaceProvider>
      </MockedProvider>,
    );

    expect(screen.getByText(/unknown/i)).toBeVisible();

    const found = await screen.findByText(/has-jobs/i);
    expect(found).toBeVisible();
  });

  it('returns `no-jobs` if no jobs found after loading', async () => {
    render(
      <MockedProvider mocks={workspaceWithNoJobs}>
        <WorkspaceProvider>
          <Test />
        </WorkspaceProvider>
      </MockedProvider>,
    );

    expect(screen.getByText(/unknown/i)).toBeVisible();

    const found = await screen.findByText(/no-jobs/i);
    expect(found).toBeVisible();
  });

  it('returns `no-jobs` if only dunder job found', async () => {
    render(
      <MockedProvider mocks={workspaceWithDunderJob}>
        <WorkspaceProvider>
          <Test />
        </WorkspaceProvider>
      </MockedProvider>,
    );

    expect(screen.getByText(/unknown/i)).toBeVisible();

    const found = await screen.findByText(/no-jobs/i);
    expect(found).toBeVisible();
  });
});
