import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {ScheduleBulkActionMenu} from '../ScheduleBulkActionMenu';
import {
  scheduleAlaskaCurrentlyStopped,
  scheduleColoradoCurrentlyStopped,
  scheduleDelawareCurrentlyRunning,
  scheduleHawaiiCurrentlyRunning,
} from '../__fixtures__/ScheduleState.fixtures';

jest.mock('../ScheduleStateChangeDialog', () => ({
  ScheduleStateChangeDialog: () => <div />,
}));

describe('ScheduleBulkActionMenu', () => {
  const expectAriaEnabled = (node: HTMLElement) => {
    expect(node).toHaveAttribute('aria-disabled', 'false');
  };

  const expectAriaDisabled = (node: HTMLElement) => {
    expect(node).toHaveAttribute('aria-disabled', 'true');
  };

  it('renders button and menu items for stopped schedules', async () => {
    render(
      <ScheduleBulkActionMenu
        schedules={[scheduleAlaskaCurrentlyStopped, scheduleColoradoCurrentlyStopped]}
        onDone={jest.fn()}
      />,
    );

    const button = screen.getByRole('button', {name: /actions/i});
    expect(button).toBeVisible();
    expect(button).toBeEnabled();

    await userEvent.click(button);

    const startItem = screen.getByRole('menuitem', {name: /start 2 schedules/i});
    expectAriaEnabled(startItem);
    const stopItem = screen.getByRole('menuitem', {name: /stop 2 schedules/i});
    expectAriaDisabled(stopItem);
  });

  it('renders button and menu items for running schedules', async () => {
    render(
      <ScheduleBulkActionMenu
        schedules={[scheduleDelawareCurrentlyRunning, scheduleHawaiiCurrentlyRunning]}
        onDone={jest.fn()}
      />,
    );

    const button = screen.getByRole('button', {name: /actions/i});
    expect(button).toBeVisible();
    expect(button).toBeEnabled();

    await userEvent.click(button);

    const startItem = screen.getByRole('menuitem', {name: /start 2 schedules/i});
    expectAriaDisabled(startItem);
    const stopItem = screen.getByRole('menuitem', {name: /stop 2 schedules/i});
    expectAriaEnabled(stopItem);
  });

  it('renders button and menu items for mixture of statuses', async () => {
    render(
      <ScheduleBulkActionMenu
        schedules={[
          scheduleAlaskaCurrentlyStopped,
          scheduleColoradoCurrentlyStopped,
          scheduleDelawareCurrentlyRunning,
          scheduleHawaiiCurrentlyRunning,
        ]}
        onDone={jest.fn()}
      />,
    );

    const button = screen.getByRole('button', {name: /actions/i});
    expect(button).toBeVisible();
    expect(button).toBeEnabled();

    await userEvent.click(button);

    // Both options enabled
    const startItem = screen.getByRole('menuitem', {name: /start 4 schedules/i});
    expectAriaEnabled(startItem);
    const stopItem = screen.getByRole('menuitem', {name: /stop 4 schedules/i});
    expectAriaEnabled(stopItem);
  });
});
