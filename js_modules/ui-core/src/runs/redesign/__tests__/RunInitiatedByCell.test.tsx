import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {RunInitiatedByCell} from '../RunInitiatedByCell';
import {
  autoRetryInBackfillRun,
  backfillChildRun,
  defaultAutomationSensorRun,
  manualRun,
  manualRunWithUser,
  reExecutionRun,
  scheduleRun,
  scheduleRunWithTick,
  scheduleRunWithoutRepo,
} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

const renderCell = (entry: MappedRunsFeedEntry, onOpenTickDetails = jest.fn()) =>
  render(
    <MemoryRouter>
      <RunInitiatedByCell entry={entry} onOpenTickDetails={onOpenTickDetails} />
    </MemoryRouter>,
  );

describe('RunInitiatedByCell', () => {
  it.each([
    ['declarative automation', defaultAutomationSensorRun, 'Declarative automation'],
    ['manual', manualRun, 'Manual'],
    ['re-execution', reExecutionRun, 'Re-execution of'],
    ['automatic retry', autoRetryInBackfillRun, 'Auto retry of'],
  ])('labels a %s initiator', async (_name, entry, label) => {
    renderCell(entry);
    expect(await screen.findByText(label)).toBeVisible();
  });

  it('links the schedule name to its schedule page', async () => {
    renderCell(scheduleRun);
    expect(await screen.findByRole('link', {name: /hourly_schedule/})).toHaveAttribute(
      'href',
      '/locations/my_repo@my_location/schedules/hourly_schedule',
    );
  });

  it('renders the schedule name as text when the repository is unknown', async () => {
    renderCell(scheduleRunWithoutRepo);
    expect(await screen.findByText('hourly_schedule')).toBeVisible();
    expect(screen.queryByRole('link', {name: /hourly_schedule/})).toBeNull();
  });

  it('links the parent run of a re-execution and keeps its user', async () => {
    renderCell(reExecutionRun);
    expect(await screen.findByRole('link', {name: 'pppppppp'})).toHaveAttribute(
      'href',
      '/runs/pppppppp-1111-2222-3333-444455556666',
    );
    expect(await screen.findByTitle('pat@example.com')).toBeVisible();
  });

  it('links the backfill a run belongs to', async () => {
    renderCell(backfillChildRun);
    expect(await screen.findByRole('link', {name: 'bkfl1234'})).toHaveAttribute(
      'href',
      '/runs/b/bkfl1234',
    );
  });

  it('shows the launching user for a manual run', async () => {
    renderCell(manualRunWithUser);
    expect(await screen.findByTitle('pat@example.com')).toBeVisible();
  });

  it('reports the tick and its button when the affordance is used', async () => {
    const user = userEvent.setup();
    const onOpenTickDetails = jest.fn();
    renderCell(scheduleRunWithTick, onOpenTickDetails);

    const button = await screen.findByRole('button', {name: 'View tick'});
    await user.click(button);

    expect(onOpenTickDetails).toHaveBeenCalledTimes(1);
    expect(onOpenTickDetails).toHaveBeenCalledWith(
      {
        tickId: 'tick-id',
        instigationSelector: {
          name: 'hourly_schedule',
          repositoryName: 'my_repo',
          repositoryLocationName: 'my_location',
        },
      },
      button,
    );
  });
});
