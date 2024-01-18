import * as React from 'react';
import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {DeploymentStatus, DeploymentStatusContext} from '../../instance/DeploymentStatusProvider';
import {DeploymentStatusIcon} from '../DeploymentStatusIcon';

describe('DeploymentStatusIcon', () => {
  it('does not show warning icon when no loading state or warnings', async () => {
    const value = {codeLocations: null, daemons: null};
    render(
      <DeploymentStatusContext.Provider value={value}>
        <DeploymentStatusIcon />
      </DeploymentStatusContext.Provider>,
    );

    expect(await screen.findByText(/no errors/i)).toBeInTheDocument();
  });

  it('shows the spinner when repo locations are loading', async () => {
    const event = userEvent.setup();
    const value: DeploymentStatus = {
      codeLocations: {type: 'spinner', content: 'Wait patiently!'},
      daemons: null,
    };

    render(
      <DeploymentStatusContext.Provider value={value}>
        <DeploymentStatusIcon />
      </DeploymentStatusContext.Provider>,
    );

    const spinner = await screen.findByTitle(/loading/i);
    expect(spinner).toBeVisible();

    await event.hover(spinner);
    expect(await screen.findByText(/wait patiently/i)).toBeVisible();
  });

  it('shows the error message when repo location warnings are found', async () => {
    const event = userEvent.setup();
    const value: DeploymentStatus = {
      codeLocations: {type: 'warning', content: 'Oh no!'},
      daemons: null,
    };

    render(
      <DeploymentStatusContext.Provider value={value}>
        <DeploymentStatusIcon />
      </DeploymentStatusContext.Provider>,
    );

    const warningIcon = await screen.findByRole('img', {name: /warning/i});
    expect(warningIcon).toBeVisible();

    await event.hover(warningIcon);
    expect(await screen.findByText(/oh no/i)).toBeVisible();
  });

  it('shows the error message when daemon warnings are found', async () => {
    const event = userEvent.setup();
    const value: DeploymentStatus = {
      codeLocations: null,
      daemons: {type: 'warning', content: 'Daemon problem!'},
    };

    render(
      <DeploymentStatusContext.Provider value={value}>
        <DeploymentStatusIcon />
      </DeploymentStatusContext.Provider>,
    );

    const warningIcon = await screen.findByRole('img', {name: /warning/i});
    expect(warningIcon).toBeVisible();

    await event.hover(warningIcon);
    expect(await screen.findByText(/daemon problem/i)).toBeVisible();
  });
});
