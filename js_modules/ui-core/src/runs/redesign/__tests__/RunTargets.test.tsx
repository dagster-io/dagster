import {render, screen, within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {buildAssetKey} from '../../../graphql/builders';
import {RunTargets} from '../RunTargets';
import {
  assetBackfill,
  assetsKnownChecksUnknownRun,
  checksKnownAssetsUnknownRun,
  checksOnlyRun,
  completeSelectionRun,
  emptyWholeJobRun,
  incompleteSelectionRun,
  jobBackfill,
  runEntry,
  unknownSelectionsRun,
} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

const renderCell = (entry: MappedRunsFeedEntry) =>
  render(
    <MemoryRouter>
      <RunTargets entry={entry} />
    </MemoryRouter>,
  );

describe('RunTargets', () => {
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
    ['the checks', assetsKnownChecksUnknownRun, '1 asset'],
    ['the assets', checksKnownAssetsUnknownRun, '1 check'],
  ])('shows only the known count when %s are unknown', async (_name, entry, label) => {
    renderCell(entry);
    const links = await screen.findAllByRole('link');
    expect(links.map((link) => link.textContent)).toEqual([label]);
  });

  it('renders nothing when both selections are unknown', () => {
    const {container} = renderCell(unknownSelectionsRun);
    expect(container.textContent).toBe('');
  });

  it('renders nothing for a run that targets the whole job', () => {
    const {container} = renderCell(emptyWholeJobRun);
    expect(container.textContent).toBe('');
  });

  it('links a count tag to the entry', async () => {
    renderCell(completeSelectionRun);
    expect(await screen.findByRole('link', {name: '3 assets'})).toHaveAttribute(
      'href',
      '/runs/complete-selection-run-id',
    );
  });

  it.each([
    ['an asset backfill', assetBackfill],
    ['a job backfill', jobBackfill],
  ])('renders nothing for %s', (_name, entry) => {
    const {container} = renderCell(entry);
    expect(container.textContent).toBe('');
  });
});
