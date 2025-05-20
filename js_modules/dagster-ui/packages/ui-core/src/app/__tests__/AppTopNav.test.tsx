import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {RecoilRoot} from 'recoil';

import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {AppTopNav} from '../AppTopNav/AppTopNav';
import {workspaceWithNoJobs} from '../__fixtures__/useJobStateForNav.fixtures';

// We don't need to render the search input here.
jest.mock('../../search/SearchDialog', () => ({
  useSearchDialog: () => ({
    openSearch: jest.fn(),
    overlay: () => <div />,
  }),
}));

describe('AppTopNav', () => {
  it('renders links and controls', async () => {
    render(
      <RecoilRoot>
        <MockedProvider mocks={[...workspaceWithNoJobs]}>
          <MemoryRouter>
            <WorkspaceProvider>
              <AppTopNav />
            </WorkspaceProvider>
          </MemoryRouter>
        </MockedProvider>
      </RecoilRoot>,
    );

    await screen.findByRole('link', {name: /runs/i});

    expect(screen.getByText('Overview').closest('a')).toHaveAttribute('href', '/overview');
    expect(screen.getByText('Runs').closest('a')).toHaveAttribute('href', '/runs');
    expect(screen.getByText('Assets').closest('a')).toHaveAttribute('href', '/assets');
    expect(screen.getByText('Deployment').closest('a')).toHaveAttribute('href', '/deployment');
  });
});
