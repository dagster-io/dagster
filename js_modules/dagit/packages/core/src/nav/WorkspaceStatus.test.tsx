import {waitFor} from '@testing-library/dom';
import {render, screen} from '@testing-library/react';
import * as React from 'react';

import {DeploymentStatusProvider, DeploymentStatusType} from '../instance/DeploymentStatusProvider';
import {TestProvider} from '../testing/TestProvider';

import {WorkspaceStatus} from './WorkspaceStatus';

describe('WorkspaceStatus', () => {
  const Test: React.FC<{mocks?: any}> = ({mocks}) => {
    return (
      <TestProvider apolloProps={{mocks}}>
        <DeploymentStatusProvider include={new Set<DeploymentStatusType>(['code-locations'])}>
          <WorkspaceStatus placeholder />
        </DeploymentStatusProvider>
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
