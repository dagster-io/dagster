import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {buildAssetKey} from '../../../graphql/builders';
import {DagsterTag} from '../../RunTag';
import {RunLaunchCell} from '../RunLaunchCell';
import {
  assetBackfill,
  autoMaterializeRun,
  autoRetryInBackfillRun,
  backfillChildRun,
  backfillEntry,
  completeSelectionRun,
  defaultAutomationSensorRun,
  emptyHiddenAssetJobRun,
  jobBackfill,
  manualRun,
  manualRunWithUser,
  partitionRangeRun,
  partitionSetBackfill,
  reExecutionRun,
  runEntry,
  scheduleRun,
  scheduleRunWithTick,
  scheduleRunWithoutRepo,
  singlePartitionRun,
  tag,
} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

const PARENT_RUN_ID = 'pppppppp-1111-2222-3333-444455556666';

const renderCell = (entry: MappedRunsFeedEntry, onOpenTickDetails = jest.fn()) =>
  render(
    <MemoryRouter>
      <RunLaunchCell entry={entry} onOpenTickDetails={onOpenTickDetails} />
    </MemoryRouter>,
  );

describe('RunLaunchCell', () => {
  it.each([
    ['declarative automation', defaultAutomationSensorRun, 'default_automation_condition_sensor'],
    ['declarative automation without a sensor', autoMaterializeRun, 'Declarative automation'],
    ['manual', manualRun, 'Manual'],
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

  it('shows the user who launched a re-execution', async () => {
    renderCell(reExecutionRun);
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

  it('reports the tick and its button when View tick is used', async () => {
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

  it('links the job a run executed', async () => {
    renderCell(completeSelectionRun);
    expect(await screen.findByRole('link', {name: 'daily_etl'})).toBeVisible();
  });

  it.each([
    ['a run of a hidden asset job', emptyHiddenAssetJobRun],
    ['an asset backfill', assetBackfill],
    ['a backfill with no recorded job', backfillEntry({id: 'bare-backfill-id'})],
  ])('names no job for %s', async (_name, entry) => {
    renderCell(entry);
    expect(await screen.findByText('Manual')).toBeVisible();
    expect(screen.queryByRole('link')).toBeNull();
  });

  it.each([
    ['a single partition key', singlePartitionRun, '2026-09-08'],
    ['a partition range', partitionRangeRun, '2026-09-01 → 2026-09-08'],
  ])('labels %s', async (_name, entry, label) => {
    renderCell(entry);
    expect(await screen.findByTitle(label)).toBeVisible();
  });

  it.each([
    ['a job backfill', jobBackfill, 'daily_etl'],
    ['a partition set backfill', partitionSetBackfill, 'daily_etl_partition_set'],
  ])('identifies %s', async (_name, entry, label) => {
    renderCell(entry);
    expect(await screen.findByText(label)).toBeVisible();
  });

  it.each([
    ['a manual re-execution', reExecutionRun, 'Re-execution of'],
    ['an automatic retry', autoRetryInBackfillRun, 'Retry of'],
  ])('labels %s and links its parent run', async (_name, entry, label) => {
    renderCell(entry);
    expect(await screen.findByText(label)).toBeVisible();
    expect(await screen.findByRole('link', {name: 'pppppppp'})).toHaveAttribute(
      'href',
      `/runs/${PARENT_RUN_ID}`,
    );
  });

  it('orders the tick, backfill, job, selection, and parent run after the initiator', async () => {
    const user = userEvent.setup();
    renderCell(
      runEntry({
        jobName: 'daily_etl',
        parentRunId: PARENT_RUN_ID,
        assetSelectionPreview: [buildAssetKey({path: ['sales', 'daily']})],
        assetSelectionCount: 1,
        tags: [
          tag(DagsterTag.ScheduleName, 'hourly_schedule'),
          tag(DagsterTag.TickId, 'tick-id'),
          tag(DagsterTag.Backfill, 'bkfl1234'),
        ],
      }),
    );

    const stops = [
      await screen.findByRole('link', {name: /hourly_schedule/}),
      await screen.findByRole('button', {name: 'View tick'}),
      await screen.findByRole('link', {name: 'bkfl1234'}),
      await screen.findByRole('link', {name: 'daily_etl'}),
      await screen.findByRole('link', {name: '1 asset'}),
      await screen.findByRole('link', {name: 'pppppppp'}),
    ];
    for (const stop of stops) {
      await user.tab();
      expect(document.activeElement).toBe(stop);
    }
  });
});
