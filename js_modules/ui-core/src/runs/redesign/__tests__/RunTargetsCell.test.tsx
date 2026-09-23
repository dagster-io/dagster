import {render, screen, within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {buildAssetKey} from '../../../graphql/builders';
import {RunTargetsCell} from '../RunTargetsCell';
import {
  assetBackfill,
  assetsKnownChecksUnknownRun,
  backfillEntry,
  checksKnownAssetsUnknownRun,
  checksOnlyRun,
  completeSelectionRun,
  emptyHiddenAssetJobRun,
  emptyWholeJobRun,
  incompleteSelectionRun,
  jobBackfill,
  partitionRangeRun,
  partitionSetBackfill,
  runEntry,
  singlePartitionRun,
  unknownSelectionsRun,
} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

const renderCell = (entry: MappedRunsFeedEntry, onViewDetails?: () => void) =>
  render(
    <MemoryRouter>
      <RunTargetsCell entry={entry} onViewDetails={onViewDetails} />
    </MemoryRouter>,
  );

describe('RunTargetsCell', () => {
  it.each([
    ['3 assets', completeSelectionRun],
    ['1 asset', assetsKnownChecksUnknownRun],
    ['2 checks', checksOnlyRun],
    ['1 check', checksKnownAssetsUnknownRun],
  ])('counts %s', async (label, entry) => {
    renderCell(entry);
    expect(await screen.findByText(label)).toBeVisible();
  });

  it('formats large counts', async () => {
    renderCell(
      runEntry({
        assetSelectionPreview: [buildAssetKey({path: ['warehouse', 'table_0']})],
        assetSelectionCount: 12000,
      }),
    );
    expect(await screen.findByText('12,000 assets')).toBeVisible();
  });

  it('shows the job ahead of the counts', async () => {
    renderCell(completeSelectionRun);
    const links = await screen.findAllByRole('link');
    expect(links.map((link) => link.textContent)).toEqual(['daily_etl', '3 assets']);
  });

  it('lists the selected assets on hover', async () => {
    const user = userEvent.setup();
    renderCell(completeSelectionRun);
    await user.hover(await screen.findByRole('link', {name: '3 assets'}));

    const tooltip = await screen.findByRole('tooltip');
    expect(within(tooltip).getByText('Selected assets')).toBeVisible();
    expect(within(tooltip).getByText('sales / daily')).toBeVisible();
    // A slash inside one path segment stays distinct from a nested key.
    expect(within(tooltip).getByText('a/b')).toBeVisible();
    expect(within(tooltip).getByText('a / b')).toBeVisible();
  });

  it('reports how many selected assets the preview leaves out', async () => {
    const user = userEvent.setup();
    renderCell(incompleteSelectionRun);
    expect(await screen.findByText('40 assets')).toBeVisible();

    await user.hover(await screen.findByRole('link', {name: '40 assets'}));
    expect(within(await screen.findByRole('tooltip')).getByText('+15 more')).toBeVisible();
  });

  it('lists the selected checks on hover', async () => {
    const user = userEvent.setup();
    renderCell(checksOnlyRun);
    await user.hover(await screen.findByRole('link', {name: '2 checks'}));

    const tooltip = await screen.findByRole('tooltip');
    expect(within(tooltip).getByText('Selected checks')).toBeVisible();
    expect(within(tooltip).getByText('freshness on sales / daily')).toBeVisible();
    expect(within(tooltip).getByText('row_count on sales / daily')).toBeVisible();
  });

  it.each([
    ['both categories', unknownSelectionsRun],
    ['the checks', assetsKnownChecksUnknownRun],
    ['the assets', checksKnownAssetsUnknownRun],
  ])('offers a way to see targets when %s are unknown', async (_name, entry) => {
    renderCell(entry);
    expect(await screen.findByRole('link', {name: 'View targets'})).toHaveAttribute(
      'href',
      entry.href,
    );
  });

  it('shows the job alone for a run that targets the whole job', async () => {
    renderCell(emptyWholeJobRun);
    expect(await screen.findByRole('link', {name: 'daily_etl'})).toBeVisible();
    expect(screen.getAllByRole('link')).toHaveLength(1);
  });

  it('renders nothing for a hidden asset job run with no recorded targets', () => {
    const {container} = renderCell(emptyHiddenAssetJobRun);
    expect(container.textContent).toBe('');
  });

  it.each([
    ['a single partition key', singlePartitionRun, '2026-09-08'],
    ['a partition range', partitionRangeRun, '2026-09-01 → 2026-09-08'],
  ])('labels %s', async (_name, entry, label) => {
    renderCell(entry);
    expect(await screen.findByTitle(label)).toBeVisible();
  });

  it('links a count tag to the entry when no dialog opener is supplied', async () => {
    renderCell(completeSelectionRun);
    expect(await screen.findByRole('link', {name: '3 assets'})).toHaveAttribute(
      'href',
      '/runs/complete-selection-run-id',
    );
  });

  it('calls the dialog opener from a count tag when one is supplied', async () => {
    const user = userEvent.setup();
    const onViewDetails = jest.fn();
    renderCell(completeSelectionRun, onViewDetails);
    await user.click(await screen.findByRole('button', {name: '3 assets'}));
    expect(onViewDetails).toHaveBeenCalledTimes(1);
  });

  it.each([
    ['a job backfill', jobBackfill, 'daily_etl'],
    ['a partition set backfill', partitionSetBackfill, 'daily_etl_partition_set'],
  ])('identifies %s', async (_name, entry, label) => {
    renderCell(entry);
    expect(await screen.findByText(label)).toBeVisible();
  });

  it.each([
    ['an asset backfill', assetBackfill],
    ['a backfill with no recorded identity', backfillEntry({id: 'bare-backfill-id'})],
  ])('renders nothing for %s', (_name, entry) => {
    const {container} = renderCell(entry);
    expect(container.textContent).toBe('');
  });
});
