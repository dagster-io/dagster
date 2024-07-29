import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import {AppTopNav} from '../AppTopNav/AppTopNav';
import {AppTopNavRightOfLogo} from '../AppTopNav/AppTopNavRightOfLogo.oss';
import {InjectedComponentContext} from '../InjectedComponentContext';

// We don't need to render the search input here.
jest.mock('../../search/SearchDialog', () => ({
  SearchDialog: () => <div />,
}));

describe('AppTopNav', () => {
  it('renders links and controls', async () => {
    render(
      <InjectedComponentContext.Provider
        value={{
          components: {
            AppTopNavRightOfLogo,
          } as any,
          hooks: {} as any,
        }}
      >
        <MockedProvider>
          <MemoryRouter>
            <AppTopNav />
          </MemoryRouter>
        </MockedProvider>
      </InjectedComponentContext.Provider>,
    );

    await screen.findByRole('link', {name: /runs/i});

    expect(screen.getByText('Overview').closest('a')).toHaveAttribute('href', '/overview');
    expect(screen.getByText('Runs').closest('a')).toHaveAttribute('href', '/runs');
    expect(screen.getByText('Assets').closest('a')).toHaveAttribute('href', '/assets');
    expect(screen.getByText('Deployment').closest('a')).toHaveAttribute('href', '/locations');
  });
});
