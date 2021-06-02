import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';
import {useRepositoryOptions} from '../workspace/WorkspaceContext';

import {RepositoryPicker} from './RepositoryPicker';

describe('RepositoryPicker', () => {
  const defaultMocks = {
    RepositoryLocation: () => ({
      isReloadSupported: true,
      name: () => 'undisclosed-location',
      repositories: () => new MockList(1),
    }),
  };

  const Test: React.FC = () => {
    const {loading, options} = useRepositoryOptions();
    return (
      <RepositoryPicker
        loading={loading}
        options={options}
        selected={options}
        toggleRepo={() => {}}
      />
    );
  };

  const Wrapper: React.FC<{mocks: any}> = (props) => {
    const {mocks} = props;
    return (
      <TestProvider apolloProps={{mocks}}>
        <Test />
      </TestProvider>
    );
  };

  it('renders the current repository and refresh button', async () => {
    const mocks = {
      Repository: () => ({
        name: () => 'foo-bar',
      }),
    };

    render(<Wrapper mocks={[defaultMocks, mocks]} />);

    await waitFor(() => {
      expect(screen.getByText(/foo-bar/i)).toBeVisible();
      expect(screen.getByRole('button', {name: /refresh/i})).toBeVisible();
    });
  });
});
