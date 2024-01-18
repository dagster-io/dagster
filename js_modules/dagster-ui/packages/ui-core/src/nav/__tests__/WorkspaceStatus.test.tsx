import * as React from 'react';
import {waitFor} from '@testing-library/dom';
import {render, screen} from '@testing-library/react';

import {DeploymentStatusContext} from '../../instance/DeploymentStatusProvider';
import {WorkspaceStatus} from '../WorkspaceStatus';

describe('WorkspaceStatus', () => {
  it('does not display if no errors', async () => {
    render(
      <DeploymentStatusContext.Provider value={{codeLocations: null, daemons: null}}>
        <WorkspaceStatus placeholder />
      </DeploymentStatusContext.Provider>,
    );

    expect(screen.queryByLabelText('warning')).toBeNull();
  });

  it('displays if any repo errors', async () => {
    render(
      <DeploymentStatusContext.Provider
        value={{codeLocations: {type: 'warning', content: 'fail'}, daemons: null}}
      >
        <WorkspaceStatus placeholder />
      </DeploymentStatusContext.Provider>,
    );

    await waitFor(() => {
      expect(screen.queryByLabelText('warning')).toBeVisible();
    });
  });
});
