import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {buildInstigationState, buildInstigationTick} from '../../../graphql/builders';
import {InstigationTickStatus, InstigationType} from '../../../graphql/types';
import {JOB_SELECTED_TICK_QUERY} from '../../../instigation/TickDetailsDialog';
import {
  SelectedTickQuery,
  SelectedTickQueryVariables,
} from '../../../instigation/types/TickDetailsDialog.types';
import {buildQueryMock} from '../../../testing/mocking';
import {RunInitiatedByCell} from '../RunInitiatedByCell';
import {
  FIXTURE_NOW_MS,
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

const tickMock = buildQueryMock<SelectedTickQuery, SelectedTickQueryVariables>({
  query: JOB_SELECTED_TICK_QUERY,
  variables: {
    instigationSelector: {
      name: 'hourly_schedule',
      repositoryName: 'my_repo',
      repositoryLocationName: 'my_location',
    },
    tickId: 'tick-id',
  },
  data: {
    instigationStateOrError: buildInstigationState({
      id: 'hourly_schedule-state-id',
      tick: buildInstigationTick({
        id: 'tick-id',
        tickId: 'tick-id',
        instigationType: InstigationType.SCHEDULE,
        status: InstigationTickStatus.SUCCESS,
        timestamp: FIXTURE_NOW_MS / 1000 - 600,
        requestedAssetMaterializationCount: 0,
        requestedJobRunCount: 1,
        runIds: [],
        originRunIds: [],
        runs: [],
        error: null,
        skipReason: null,
      }),
    }),
  },
});

const renderCell = (entry: MappedRunsFeedEntry) =>
  render(
    <MemoryRouter>
      <MockedProvider mocks={[tickMock]}>
        <RunInitiatedByCell entry={entry} />
      </MockedProvider>
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

  it('opens the tick details dialog from the tick affordance', async () => {
    const user = userEvent.setup();
    renderCell(scheduleRunWithTick);
    await user.click(await screen.findByRole('button', {name: 'View tick'}));
    expect(await screen.findByText(/Tick for hourly_schedule/)).toBeVisible();
  });
});
