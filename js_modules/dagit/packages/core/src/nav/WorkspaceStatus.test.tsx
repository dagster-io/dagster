import {waitFor} from '@testing-library/dom';
import {render, screen} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';

import {WorkspaceStatus} from './WorkspaceStatus';

describe('WorkspaceStatus', () => {
  const Test: React.FC<{mocks?: any}> = ({mocks}) => {
    return (
      <TestProvider apolloProps={{mocks}}>
        <WorkspaceStatus />
      </TestProvider>
    );
  };

  it('does not display if no errors', async () => {
    render(<Test />);
    await waitFor(() => {
      expect(screen.queryByLabelText('warning')).toBeNull();
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
      expect(screen.queryByLabelText('warning')).toBeVisible();
    });
  });
});
