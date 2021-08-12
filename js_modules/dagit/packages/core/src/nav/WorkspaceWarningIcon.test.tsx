import {waitFor} from '@testing-library/dom';
import {render, screen} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';

import {WorkspaceWarningIcon} from './WorkspaceWarningIcon';

describe('WorkspaceWarningIcon', () => {
  const Test: React.FC<{mocks?: any}> = ({mocks}) => {
    return (
      <TestProvider apolloProps={{mocks}}>
        <WorkspaceWarningIcon />
      </TestProvider>
    );
  };

  it('does not display if no errors', async () => {
    render(<Test />);
    await waitFor(() => {
      expect(screen.queryByText(/warnings found/i)).toBeNull();
    });
  });

  it('displays if any repo errors', async () => {
    const mocks = {
      RepositoryLocationOrLoadError: () => ({
        __typename: 'PythonError',
        message: () => 'Failure',
      }),
    };
    render(<Test mocks={mocks} />);
    await waitFor(() => {
      expect(screen.getByText(/warnings found/i)).toBeVisible();
    });
  });
});
